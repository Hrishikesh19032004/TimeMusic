# Spotify Playlist Analyzer

A Python-based web scraping tool that analyzes Spotify playlists by extracting detailed metadata and track information without requiring API access. The analyzer uses Selenium WebDriver for dynamic content loading and BeautifulSoup for HTML parsing.

## Overview

This tool scrapes public Spotify playlist pages to extract comprehensive playlist information including metadata, track details, and listening statistics. It's designed to work with Spotify's web interface and handles dynamic content loading through automated browser interaction.

## Features

- **Playlist Metadata Extraction**: Name, description, total songs, duration, and save counts
- **Track Information**: Song names, artists, albums, durations, release years, and date added
- **Hybrid Scraping Approach**: Combines DOM parsing with regex pattern matching for robust data extraction
- **Data Export**: Saves analysis results in structured JSON format
- **Debug Capabilities**: Saves HTML snapshots for troubleshooting
- **Headless Operation**: Runs without GUI for server deployment

## Technical Approach

### 1. Multi-Strategy Data Extraction

The analyzer employs a hybrid approach to overcome Spotify's dynamic content loading:

- **Primary Method**: Selenium WebDriver with Chrome for JavaScript execution
- **Secondary Method**: BeautifulSoup for HTML structure parsing
- **Fallback Method**: Regex pattern matching on raw HTML content

### 2. Robust Selector Strategy

Uses multiple CSS selectors for each data point to handle Spotify's frequent UI changes:

```python
# Example: Multiple selectors for playlist name
name_selectors = [
    'h1[data-testid="entityTitle"]',
    'h1.Type__TypeElement-sc-goli3j-0',
    'h1[data-encore-id="type"]',
    'h1.encore-text',
    # ... more fallback selectors
]
```

### 3. Content Loading Management

- Implements intelligent scrolling to trigger lazy-loaded content
- Uses explicit waits for dynamic elements
- Handles timeout scenarios gracefully

## Data Flow

```
1. URL Input
   ↓
2. Browser Initialization (Chrome + Selenium)
   ↓
3. Page Loading & Wait Strategies
   ↓
4. Content Discovery (Scrolling + Dynamic Loading)
   ↓
5. Hybrid Data Extraction
   ├── DOM Parsing (BeautifulSoup)
   ├── Regex Pattern Matching
   └── JSON Data Extraction
   ↓
6. Data Validation & Cleaning
   ↓
7. Structure Assembly
   ↓
8. Export (JSON + Debug Files)
```

### Detailed Data Flow Steps

#### Phase 1: Initialization
- Sets up Chrome WebDriver with optimized options
- Configures user agent and browser settings
- Creates output directory structure

#### Phase 2: Page Loading
- Navigates to playlist URL
- Waits for playlist-specific elements to load
- Implements multiple loading detection strategies

#### Phase 3: Content Discovery
- Performs controlled scrolling to load additional tracks
- Triggers lazy-loaded content through viewport manipulation
- Captures full page state for processing

#### Phase 4: Data Extraction

**Playlist Metadata Extraction:**
- Uses cascading selector priority for robustness
- Extracts: name, description, song count, duration, saves
- Validates data against common patterns

**Track Information Extraction:**
- Identifies track container elements
- Extracts per-track data: name, artists, album, duration
- Cross-references with JSON data embedded in page

**Duration Processing:**
- Extracts duration data from multiple sources
- Normalizes format (mm:ss)
- Calculates total playlist duration

#### Phase 5: Data Assembly
- Combines metadata and track information
- Applies data validation and cleaning
- Limits output to top 20 tracks for performance

#### Phase 6: Output Generation
- Structures data in standardized JSON format
- Saves debug HTML for troubleshooting
- Generates human-readable summary

## Installation

```bash
# Install required packages
pip install selenium beautifulsoup4 requests

# Install ChromeDriver
# Download from: https://chromedriver.chromium.org/
# Or use: brew install chromedriver (macOS)
```

## Usage

### Basic Usage

```python
from spotify_analyzer import SpotifyPlaylistAnalyzer

# Initialize analyzer
analyzer = SpotifyPlaylistAnalyzer(headless=True)

# Analyze playlist
playlist_url = "https://open.spotify.com/playlist/YOUR_PLAYLIST_ID"
analysis = analyzer.analyze_playlist(playlist_url)

# Print summary
analyzer.print_summary(analysis)

# Save results
analyzer.save_analysis(analysis)

# Clean up
analyzer.close()
```

### Command Line Usage

```bash
python spotify_analyzer.py
```

## Output Format

The analyzer generates structured JSON output:

```json
{
  "type": "playlist",
  "timestamp": "2024-01-01T12:00:00.000000",
  "url": "playlist_url",
  "playlist_metadata": {
    "name": "Playlist Name",
    "description": "Playlist description",
    "number_of_songs": 50,
    "total_duration": "3:25:30",
    "total_saves": "1,234"
  },
  "tracks_analyzed": 20,
  "tracks": [
    {
      "track_name": "Song Name",
      "artists": ["Artist 1", "Artist 2"],
      "album_name": "Album Name",
      "duration": "3:45",
      "release_year": "2023",
      "date_added": "2024-01-01",
      "streams": "N/A"
    }
  ]
}
```

## Error Handling

The analyzer includes comprehensive error handling:

- **Network Issues**: Retry mechanisms and timeout handling
- **Missing Elements**: Graceful degradation with fallback selectors
- **Data Validation**: Type checking and format normalization
- **Debug Support**: HTML snapshots and detailed logging

## Limitations

- **Rate Limiting**: Respects reasonable request intervals
- **Public Playlists Only**: Cannot access private playlists
- **Track Limit**: Limited to top 20 tracks per playlist for performance
- **Browser Dependency**: Requires Chrome/Chromium installation
- **Dynamic UI**: May need updates if Spotify changes their interface

## Architecture Decisions

### Why Selenium Over Pure HTTP Requests?
- Spotify's heavy use of JavaScript for content loading
- Dynamic DOM manipulation requires browser execution
- Handles anti-bot measures through real browser behavior

### Why Hybrid Extraction Approach?
- Single method often fails due to UI variations
- Multiple strategies ensure data extraction success
- Fallback mechanisms improve reliability

## Dependencies

- `selenium`: Web browser automation
- `beautifulsoup4`: HTML parsing and navigation
- `requests`: HTTP request handling
- `json`: Data serialization
- `re`: Regular expression pattern matching
- `os`: File system operations
- `datetime`: Timestamp generation
- `time`: Execution flow control

## Troubleshooting

### Common Issues

1. **ChromeDriver Path Issues**
   - Ensure ChromeDriver is in PATH or specify location
   - Match ChromeDriver version with installed Chrome

2. **Timeout Errors**
   - Increase wait times for slower connections
   - Check if playlist URL is accessible

3. **No Data Extracted**
   - Verify playlist is public
   - Check debug HTML file for page structure changes

4. **Incomplete Track Data**
   - Some tracks may have limited metadata
   - Cross-reference with multiple data sources

