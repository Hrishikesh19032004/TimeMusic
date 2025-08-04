import requests
import json
import os
from datetime import datetime
import time
import re
from urllib.parse import urlparse, parse_qs
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from bs4 import BeautifulSoup

class SpotifyPlaylistAnalyzer:
    def __init__(self, headless=True):
        """Initialize the analyzer with Selenium WebDriver."""
        self.results_dir = "SpotifyData"
        os.makedirs(self.results_dir, exist_ok=True)
        
        # Setup Chrome options
        chrome_options = Options()
        if headless:
            chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        # Initialize driver
        self.driver = webdriver.Chrome(options=chrome_options)
        self.wait = WebDriverWait(self.driver, 30)

    def extract_playlist_id(self, url):
        """Extract playlist ID from Spotify URL."""
        if "playlist/" in url:
            return url.split("playlist/")[1].split("?")[0]
        return None

    def format_duration(self, duration_ms):
        """Convert milliseconds to mm:ss format."""
        if not duration_ms:
            return "0:00"
        
        try:
            seconds = int(duration_ms / 1000)
            minutes = seconds // 60
            seconds = seconds % 60
            return f"{minutes}:{seconds:02d}"
        except:
            return "0:00"

    def parse_duration_text(self, duration_text):
        """Parse duration text like '3:45' to seconds."""
        if not duration_text or ':' not in duration_text:
            return 0
        
        try:
            parts = duration_text.split(':')
            if len(parts) == 2:
                minutes = int(parts[0])
                seconds = int(parts[1])
                return (minutes * 60) + seconds
        except:
            return 0
        return 0

    def get_release_year(self, release_date):
        """Extract year from release date."""
        if not release_date:
            return "Unknown"
        try:
            return release_date.split("-")[0]
        except:
            return "Unknown"

    def parse_date_added(self, date_string):
        """Parse and format date added."""
        if not date_string:
            return "Unknown"
        
        try:
            # Handle different date formats
            if 'T' in date_string:
                # ISO format: 2023-12-01T00:00:00Z
                date_part = date_string.split('T')[0]
                return date_part
            elif len(date_string) == 10 and date_string.count('-') == 2:
                # Already in YYYY-MM-DD format
                return date_string
            else:
                # Try to parse other formats
                return date_string
        except:
            return "Unknown"

    def scroll_and_load_tracks(self):
        """Scroll down to load more tracks if needed."""
        try:
            # Scroll to load at least 20 tracks
            for i in range(5):  # Increased scrolling
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(3)  # Increased wait time
            
            # Scroll back to top
            self.driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(2)
            
        except Exception as e:
            print(f"Error during scrolling: {str(e)}")

    def extract_durations_from_html(self, html_content):
        """Extract durations using regex patterns from HTML."""
        durations = []
        
        # Look for duration patterns in the HTML
        duration_patterns = [
            r'(\d+:\d{2})',  # Simple mm:ss pattern
            r'"duration_ms":(\d+)',  # JSON duration in milliseconds
            r'"duration":\s*(\d+)',  # Alternative duration format
        ]
        
        for pattern in duration_patterns:
            matches = re.findall(pattern, html_content)
            if matches:
                if 'duration_ms' in pattern or '"duration"' in pattern:
                    # Convert milliseconds to mm:ss
                    durations = [self.format_duration(int(ms)) for ms in matches]
                else:
                    durations = matches
                break
        
        return durations

    def scrape_playlist_data(self, playlist_url):
        """Hybrid scraping approach combining both methods."""
        print(f"Scraping playlist: {playlist_url}")
        
        try:
            # Load the playlist page
            self.driver.get(playlist_url)
            print("Page loaded, waiting for content...")
            time.sleep(10)  # Increased wait time
            
            # Try to wait for playlist content
            try:
                self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "[data-testid='playlist-page']")))
                print("Playlist page detected")
            except TimeoutException:
                print("Playlist page selector not found, trying alternatives...")
                try:
                    self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "main")))
                    print("Main content detected")
                except TimeoutException:
                    print("Warning: Could not detect page structure, continuing anyway...")
            
            # Scroll to load more tracks
            self.scroll_and_load_tracks()
            
            # Get page source
            html_content = self.driver.page_source
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Save debug HTML
            debug_file = os.path.join(self.results_dir, f"debug_page_{int(time.time())}.html")
            with open(debug_file, 'w', encoding='utf-8') as f:
                f.write(html_content)
            print(f"Debug HTML saved to: {debug_file}")
            
            # Extract playlist metadata using the working method
            playlist_metadata = self.extract_playlist_metadata(soup, html_content)
            
            # Extract track data using hybrid approach
            tracks_data = self.extract_tracks_hybrid(soup, html_content)
            
            return {
                "playlist_metadata": playlist_metadata,
                "tracks": tracks_data[:20]  # Limit to top 20 tracks
            }
            
        except Exception as e:
            print(f"Error scraping playlist: {str(e)}")
            import traceback
            traceback.print_exc()
            return None

    def extract_playlist_metadata(self, soup, html_content):
        """Extract playlist metadata using enhanced selectors."""
        metadata = {
            "name": "Unknown",
            "description": "",
            "total_saves": "N/A",
            "number_of_songs": 0,
            "total_duration": "0:00"
        }
        
        try:
            # Enhanced playlist name extraction
            name_selectors = [
                'h1[data-testid="entityTitle"]',
                'h1.Type__TypeElement-sc-goli3j-0',
                'h1[data-encore-id="type"]',
                'h1.encore-text',
                'span[data-testid="entityTitle"]',
                'h1',
                '.main-entityHeader-title',
                '[data-testid="entityTitle"]'
            ]
            
            for selector in name_selectors:
                title_elem = soup.select_one(selector)
                if title_elem and title_elem.get_text(strip=True):
                    name = title_elem.get_text(strip=True)
                    if name not in ['Your Library', 'Spotify', '']:
                        metadata["name"] = name
                        print(f"Found playlist name: {metadata['name']}")
                        break
            
            # Enhanced description extraction with more patterns
            desc_selectors = [
                '[data-testid="description"]',
                'span[data-testid="description"]',
                '.Type__TypeElement-sc-goli3j-0.fZDcWX',
                'span[data-encore-id="text"].Type__TypeElement-sc-goli3j-0',
                '.main-entityHeader-subtitle',
                'div[data-testid="playlist-description"]',
                'p[data-encore-id="text"]',
                '[data-testid="entitySubtitle"]',
                '.main-entityHeader-subtitle span'
            ]
            
            for selector in desc_selectors:
                desc_elem = soup.select_one(selector)
                if desc_elem and desc_elem.get_text(strip=True):
                    description = desc_elem.get_text(strip=True)
                    # Filter out common non-description text
                    if (len(description) > 5 and 
                        description not in ['Made for you', 'By Spotify', 'Spotify', metadata["name"]] and
                        not description.isdigit() and
                        'songs' not in description.lower() and
                        'tracks' not in description.lower()):
                        metadata["description"] = description
                        print(f"Found description: {description[:50]}...")
                        break
            
            # Try to extract description from JSON data
            if metadata["description"] == "":
                json_desc_patterns = [
                    r'"description":\s*"([^"]+)"',
                    r'"subtitle":\s*"([^"]+)"'
                ]
                
                for pattern in json_desc_patterns:
                    matches = re.findall(pattern, html_content)
                    if matches:
                        for desc in matches:
                            if (len(desc) > 5 and 
                                desc not in ['Made for you', 'By Spotify', 'Spotify', metadata["name"]] and
                                not desc.isdigit()):
                                metadata["description"] = desc
                                print(f"Found description from JSON: {desc[:50]}...")
                                break
                        if metadata["description"]:
                            break
            
            # Enhanced saves/likes extraction
            page_text = soup.get_text()
            
            saves_patterns = [
                r'(\d{1,3}(?:,\d{3})*)\s+saves?',
                r'(\d{1,3}(?:,\d{3})*)\s+likes?',
                r'(\d+)\s+saves?',
                r'(\d+)\s+likes?',
                r'"followers":\s*{\s*"total":\s*(\d+)',
                r'follower.*?(\d{1,3}(?:,\d{3})*)',
                r'save.*?(\d{1,3}(?:,\d{3})*)'
            ]
            
            for pattern in saves_patterns:
                matches = re.findall(pattern, page_text, re.IGNORECASE)
                if not matches:
                    matches = re.findall(pattern, html_content, re.IGNORECASE)
                
                if matches:
                    saves_count = matches[0]
                    if isinstance(saves_count, str) and (saves_count.isdigit() or ',' in saves_count):
                        metadata["total_saves"] = saves_count
                        print(f"Found saves: {saves_count}")
                        break
            
            # Enhanced song count extraction
            song_patterns = [
                r'(\d{1,3}(?:,\d{3})*)\s+songs?',
                r'(\d+)\s+songs?',
                r'(\d{1,3}(?:,\d{3})*)\s+tracks?',
                r'(\d+)\s+tracks?'
            ]
            
            for pattern in song_patterns:
                matches = re.findall(pattern, page_text, re.IGNORECASE)
                if matches:
                    count = matches[0].replace(',', '') if ',' in str(matches[0]) else matches[0]
                    metadata["number_of_songs"] = int(count)
                    print(f"Found song count: {count}")
                    break
            
            # Enhanced duration extraction
            duration_patterns = [
                r'(\d+)\s+hr\s+(\d+)\s+min',
                r'(\d+)\s+hours?\s+(\d+)\s+minutes?',
                r'(\d+)\s+min\s+(\d+)\s+sec',
                r'(\d+)\s+minutes?\s+(\d+)\s+seconds?',
                r'(\d+)\s+min',
                r'(\d+)\s+minutes?'
            ]
            
            for pattern in duration_patterns:
                matches = re.findall(pattern, page_text, re.IGNORECASE)
                if matches:
                    match = matches[0]
                    if isinstance(match, tuple) and len(match) == 2:
                        first, second = match
                        if 'hr' in pattern or 'hour' in pattern:
                            hours, minutes = int(first), int(second)
                            metadata["total_duration"] = f"{hours}:{minutes:02d}:00"
                        else:
                            minutes, seconds = int(first), int(second)
                            metadata["total_duration"] = f"{minutes}:{seconds:02d}"
                    else:
                        minutes = int(match) if isinstance(match, str) else int(match[0])
                        metadata["total_duration"] = f"0:{minutes:02d}:00"
                    print(f"Found duration: {metadata['total_duration']}")
                    break
            
        except Exception as e:
            print(f"Error extracting playlist metadata: {str(e)}")
        
        return metadata

    def extract_tracks_hybrid(self, soup, html_content):
        """Hybrid method: Get track info from HTML structure and durations from regex."""
        tracks = []
        
        try:
            # First, extract durations from HTML content using regex
            durations = self.extract_durations_from_html(html_content)
            print(f"Found {len(durations)} durations: {durations[:5]}...")  # Show first 5
            
            # Extract release years and dates from JSON data
            release_years = self.extract_release_years_from_json(html_content)
            dates_added = self.extract_dates_added_from_json(html_content)
            
            print(f"Found {len(release_years)} release years")
            print(f"Found {len(dates_added)} dates added")
            
            # Then extract track info using BeautifulSoup (the working method)
            track_selectors = [
                '[data-testid="tracklist-row"]',
                '[data-testid="track-row"]',
                'div[role="row"]'
            ]
            
            track_rows = []
            for selector in track_selectors:
                track_rows = soup.select(selector)
                if track_rows:
                    print(f"Found {len(track_rows)} track rows using selector: {selector}")
                    break
            
            # If no track rows found, try alternative approach
            if not track_rows:
                print("No track rows found with standard selectors, trying JSON extraction...")
                return self.extract_tracks_from_json(html_content, durations, release_years, dates_added)
            
            # Process each track row
            for i, row in enumerate(track_rows[:20]):  # Limit to 20 tracks
                track_data = {
                    "track_name": "Unknown",
                    "album_name": "Unknown",
                    "date_added": dates_added[i] if i < len(dates_added) else "Unknown",
                    "duration": durations[i] if i < len(durations) else "0:00",
                    "artists": [],
                    "release_year": release_years[i] if i < len(release_years) else "Unknown",
                    "streams": "N/A"
                }
                
                try:
                    # Track name - try multiple approaches
                    track_name_selectors = [
                        '[data-testid="internal-track-link"]',
                        'a[href*="/track/"]',
                        'div[data-testid="internal-track-link"]'
                    ]
                    
                    for selector in track_name_selectors:
                        track_elem = row.select_one(selector)
                        if track_elem and track_elem.get_text(strip=True):
                            track_data["track_name"] = track_elem.get_text(strip=True)
                            break
                    
                    # Artists
                    artist_links = row.select('a[href*="/artist/"]')
                    if artist_links:
                        track_data["artists"] = [link.get_text(strip=True) for link in artist_links if link.get_text(strip=True)]
                    
                    # Album name
                    album_link = row.select_one('a[href*="/album/"]')
                    if album_link and album_link.get_text(strip=True):
                        track_data["album_name"] = album_link.get_text(strip=True)
                    
                    # If duration not found from regex, try to extract from row
                    if track_data["duration"] == "0:00":
                        duration_pattern = re.compile(r'\d+:\d{2}')
                        duration_text = row.find(string=duration_pattern)
                        if duration_text:
                            track_data["duration"] = duration_text.strip()
                    
                    # Date added - try to get from row if not found in JSON
                    if track_data["date_added"] == "Unknown":
                        date_elem = row.find('time')
                        if date_elem:
                            datetime_attr = date_elem.get('datetime')
                            if datetime_attr:
                                track_data["date_added"] = self.parse_date_added(datetime_attr)
                    
                    print(f"Extracted track {i+1}: {track_data['track_name']} by {', '.join(track_data['artists'])} ({track_data['duration']}) - {track_data['release_year']}")
                    tracks.append(track_data)
                    
                except Exception as e:
                    print(f"Error extracting track {i+1}: {str(e)}")
                    tracks.append(track_data)  # Add even with missing data
                    continue
                    
        except Exception as e:
            print(f"Error in hybrid track extraction: {str(e)}")
        
        return tracks

    def extract_release_years_from_json(self, html_content):
        """Extract release years from JSON data in HTML."""
        release_years = []
        
        try:
            # Look for album release dates in JSON
            patterns = [
                r'"album":\s*{[^}]*"release_date":\s*"([^"]+)"',
                r'"release_date":\s*"([^"]+)"',
                r'"releaseDate":\s*"([^"]+)"'
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, html_content)
                if matches:
                    release_years = [self.get_release_year(date) for date in matches]
                    print(f"Found release years using pattern: {pattern[:30]}...")
                    break
            
        except Exception as e:
            print(f"Error extracting release years: {str(e)}")
        
        return release_years

    def extract_dates_added_from_json(self, html_content):
        """Extract dates added from JSON data in HTML."""
        dates_added = []
        
        try:
            # Look for added_at dates in JSON
            patterns = [
                r'"added_at":\s*"([^"]+)"',
                r'"addedAt":\s*"([^"]+)"',
                r'"dateAdded":\s*"([^"]+)"'
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, html_content)
                if matches:
                    dates_added = [self.parse_date_added(date) for date in matches]
                    print(f"Found dates added using pattern: {pattern[:30]}...")
                    break
            
        except Exception as e:
            print(f"Error extracting dates added: {str(e)}")
        
        return dates_added

    def extract_tracks_from_json(self, html_content, durations, release_years, dates_added):
        """Fallback method: Extract tracks from JSON data in HTML."""
        tracks = []
        
        try:
            # Look for JSON patterns in the HTML
            json_patterns = [
                r'"track":\s*{[^}]*"name":\s*"([^"]+)"[^}]*"artists":\s*\[([^\]]+)\][^}]*"album":\s*{[^}]*"name":\s*"([^"]+)"',
                r'"name":\s*"([^"]+)"[^}]*"artists":\s*\[([^\]]+)\]',
                r'{"name":"([^"]+)".*?"artists":\[([^\]]+)\].*?"album":{"name":"([^"]+)"'
            ]
            
            for pattern in json_patterns:
                matches = re.findall(pattern, html_content)
                if matches:
                    print(f"Found {len(matches)} tracks using JSON pattern")
                    for i, match in enumerate(matches[:20]):
                        track_data = {
                            "track_name": match[0] if len(match) > 0 else "Unknown",
                            "album_name": match[2] if len(match) > 2 else "Unknown",
                            "date_added": dates_added[i] if i < len(dates_added) else "Unknown",
                            "duration": durations[i] if i < len(durations) else "0:00",
                            "artists": [],
                            "release_year": release_years[i] if i < len(release_years) else "Unknown",
                            "streams": "N/A"
                        }
                        
                        # Parse artists from JSON
                        if len(match) > 1:
                            artists_json = match[1]
                            artist_names = re.findall(r'"name":\s*"([^"]+)"', artists_json)
                            track_data["artists"] = artist_names
                        
                        tracks.append(track_data)
                    break
            
        except Exception as e:
            print(f"Error extracting tracks from JSON: {str(e)}")
        
        return tracks

    def calculate_total_duration(self, tracks):
        """Calculate total duration from track durations."""
        total_seconds = 0
        
        for track in tracks:
            duration = track.get("duration", "0:00")
            track_seconds = self.parse_duration_text(duration)
            total_seconds += track_seconds
        
        # Convert back to hours:minutes:seconds
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        
        if hours > 0:
            return f"{hours}:{minutes:02d}:{seconds:02d}"
        else:
            return f"{minutes}:{seconds:02d}"

    def analyze_playlist(self, playlist_url, get_detailed_metadata=False):
        """Main method to analyze a Spotify playlist."""
        print(f"Starting analysis of playlist: {playlist_url}")
        
        # Extract playlist data
        playlist_data = self.scrape_playlist_data(playlist_url)
        
        if not playlist_data:
            return {"error": "Failed to scrape playlist data"}
        
        # Calculate duration from tracks if available
        if playlist_data["tracks"]:
            calculated_duration = self.calculate_total_duration(playlist_data["tracks"])
            if calculated_duration != "0:00":
                playlist_data["playlist_metadata"]["calculated_duration"] = calculated_duration
        
        # Prepare final analysis
        analysis = {
            "type": "playlist",
            "timestamp": datetime.now().isoformat(),
            "url": playlist_url,
            "playlist_metadata": playlist_data["playlist_metadata"],
            "tracks_analyzed": len(playlist_data["tracks"]),
            "tracks": playlist_data["tracks"]
        }
        
        return analysis

    def save_analysis(self, analysis, filename=None):
        """Save analysis to JSON file."""
        if not filename:
            playlist_name = analysis["playlist_metadata"]["name"].replace(" ", "_")
            playlist_name = re.sub(r'[^\w\-_]', '', playlist_name)
            filename = f"{playlist_name}.json"
        
        filepath = os.path.join(self.results_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(analysis, f, indent=2, ensure_ascii=False)
        
        print(f"Analysis saved to: {filepath}")
        return filepath

    def print_summary(self, analysis):
        """Print a summary of the analysis."""
        if "error" in analysis:
            print(f"Error: {analysis['error']}")
            return
        
        metadata = analysis["playlist_metadata"]
        tracks = analysis["tracks"]
        
        print("\n" + "="*70)
        print("SPOTIFY PLAYLIST ANALYSIS SUMMARY")
        print("="*70)
        
        print(f"Playlist Name: {metadata['name']}")
        print(f"Description: {metadata['description']}")
        print(f"Total Songs: {metadata['number_of_songs']}")
        print(f"Total Duration: {metadata['total_duration']}")
        
        if metadata.get('calculated_duration'):
            print(f"Calculated Duration: {metadata['calculated_duration']}")
            
        print(f"Total Saves: {metadata['total_saves']}")
        print(f"Tracks Analyzed: {len(tracks)}")
        
        if tracks:
            print(f"\nTOP {len(tracks)} TRACKS:")
            print("-" * 70)
            
            for i, track in enumerate(tracks, 1):
                artists = ", ".join(track["artists"]) if track["artists"] else "Unknown"
                print(f"{i:2d}. {track['track_name']}")
                print(f"    Artist(s): {artists}")
                print(f"    Album: {track['album_name']}")
                print(f"    Duration: {track['duration']}")
                print(f"    Release Year: {track.get('release_year', 'Unknown')}")
                if track.get('date_added', 'Unknown') != 'Unknown':
                    print(f"    Date Added: {track['date_added']}")
                print()
        else:
            print("\nNo tracks found")

    def close(self):
        """Close the WebDriver."""
        if self.driver:
            self.driver.quit()

if __name__ == "__main__":
    analyzer = None
    
    try:
        print("Initializing Spotify Playlist Analyzer...")
        analyzer = SpotifyPlaylistAnalyzer(headless=True)
        
        playlist_url = "https://open.spotify.com/playlist/37i9dQZF1DWUAOn5dYbrDa"
        
        print("Starting playlist analysis...")
        analysis = analyzer.analyze_playlist(playlist_url)
        
        analyzer.print_summary(analysis)
        
        if "error" not in analysis:
            analyzer.save_analysis(analysis)
            print("Analysis completed successfully!")
        else:
            print("Analysis failed!")
            
    except KeyboardInterrupt:
        print("\nAnalysis interrupted by user")
        
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
        
    finally:
        if analyzer:
            analyzer.close()
        print("Process finished")