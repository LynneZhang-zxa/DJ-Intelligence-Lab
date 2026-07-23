import {
  useCallback,
  useEffect,
  useRef,
  useState,
} from "react";
import "./App.css";
import PlaybackWave from "./components/PlaybackWave";
import PlaylistPage from "./components/PlaylistPage";
import Spectrogram from "./components/Spectrogram";
import SpotifyPlayer from "./components/SpotifyPlayer";
import Waveform from "./components/Waveform";

const sidebarItems = [
  ["≋", "Analyze Track"],
  ["♬", "Library"],
  ["◷", "History"],
  ["▣", "Batch Analysis"],
  ["♫", "Playlists"],
  ["⚙", "Settings"],
];

const API_BASE_URL = "http://127.0.0.1:8000";

function formatTrackDuration(duration) {
  if (!Number.isFinite(duration)) {
    return "—";
  }

  const totalSeconds = Math.round(duration);
  const minutes = Math.floor(totalSeconds / 60);
  const seconds = totalSeconds % 60;
  return `${minutes}:${seconds.toString().padStart(2, "0")}`;
}

function App() {

  const initialView = new URLSearchParams(
    window.location.search
  ).get("view");
  const [activeView, setActiveView] = useState(
    initialView === "library" ? "Library" : "Analyze Track"
  );
  const [file, setFile] = useState(null);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [libraryTracks, setLibraryTracks] = useState([]);
  const [libraryLoading, setLibraryLoading] = useState(false);
  const [libraryError, setLibraryError] = useState("");
  const [importing, setImporting] = useState(false);
  const [selectedTrack, setSelectedTrack] = useState(null);
  const [playingTrackId, setPlayingTrackId] = useState(null);
  const [spotifyPlayerReady, setSpotifyPlayerReady] = useState(false);
  const [playlists, setPlaylists] = useState([]);
  const [playlistsLoading, setPlaylistsLoading] = useState(false);
  const [playlistsError, setPlaylistsError] = useState("");
  const [playlistTrackTarget, setPlaylistTrackTarget] = useState(null);
  const [targetPlaylistId, setTargetPlaylistId] = useState("");
  const [addingToPlaylist, setAddingToPlaylist] = useState(false);
  const spotifyPlayerRef = useRef(null);


  const loadLibrary = useCallback(async () => {
    setLibraryLoading(true);
    setLibraryError("");

    try {
      const response = await fetch(`${API_BASE_URL}/library`);
      if (!response.ok) {
        throw new Error("Could not load your music library.");
      }
      const tracks = await response.json();
      setLibraryTracks(tracks);
      setSelectedTrack((currentTrack) => (
        currentTrack || tracks[0] || null
      ));
    } catch (error) {
      setLibraryError(error.message);
    } finally {
      setLibraryLoading(false);
    }
  }, []);

  const loadPlaylists = useCallback(async () => {
    setPlaylistsLoading(true);
    setPlaylistsError("");

    try {
      const response = await fetch(`${API_BASE_URL}/playlists`);
      if (!response.ok) {
        throw new Error("Could not load your playlists.");
      }
      setPlaylists(await response.json());
    } catch (error) {
      setPlaylistsError(error.message);
    } finally {
      setPlaylistsLoading(false);
    }
  }, []);


  useEffect(() => {
    if (activeView === "Library") {
      const loadTimer = window.setTimeout(
        loadLibrary,
        0
      );
      return () => window.clearTimeout(loadTimer);
    }
  }, [activeView, loadLibrary]);

  useEffect(() => {
    if (
      activeView === "Library"
      || activeView === "Playlists"
    ) {
      const loadTimer = window.setTimeout(
        loadPlaylists,
        0
      );
      return () => window.clearTimeout(loadTimer);
    }
  }, [activeView, loadPlaylists]);


  const connectSpotify = () => {
    window.location.href = `${API_BASE_URL}/auth/spotify/login`;
  };


  const toggleLibraryTrack = (track) => {
    if (!spotifyPlayerReady) {
      return;
    }

    if (playingTrackId === track.spotify_id) {
      spotifyPlayerRef.current?.pause();
      setPlayingTrackId(null);
      return;
    }

    setSelectedTrack(track);
    spotifyPlayerRef.current?.playTrack(track);
    setPlayingTrackId(track.spotify_id);
  };

  const addTrackToPlaylist = async () => {
    if (!playlistTrackTarget || !targetPlaylistId) {
      return;
    }

    setAddingToPlaylist(true);
    setLibraryError("");

    try {
      const response = await fetch(
        `${API_BASE_URL}/playlists/${targetPlaylistId}/tracks`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            library_track_id: playlistTrackTarget.id,
          }),
        }
      );
      const data = await response.json();
      if (!response.ok) {
        throw new Error(
          data.detail || "Could not add track to playlist."
        );
      }

      setPlaylistTrackTarget(null);
      setTargetPlaylistId("");
      await loadPlaylists();
    } catch (error) {
      setLibraryError(error.message);
    } finally {
      setAddingToPlaylist(false);
    }
  };


  const importSpotifyLibrary = useCallback(async () => {
    setImporting(true);
    setLibraryError("");

    try {
      const response = await fetch(
        `${API_BASE_URL}/library/import/spotify`,
        { method: "POST" }
      );
      const data = await response.json();
      if (!response.ok) {
        throw new Error(
          data.detail || "Spotify import failed."
        );
      }
      await loadLibrary();
    } catch (error) {
      setLibraryError(error.message);
    } finally {
      setImporting(false);
    }
  }, [loadLibrary]);


  useEffect(() => {
    const callbackParams = new URLSearchParams(
      window.location.search
    );

    if (callbackParams.get("spotify") !== "connected") {
      return;
    }

    window.history.replaceState(
      {},
      "",
      window.location.pathname
    );

    const importTimer = window.setTimeout(
      importSpotifyLibrary,
      0
    );

    return () => window.clearTimeout(importTimer);
  }, [importSpotifyLibrary]);


  const analyzeAudio = async () => {

    if (!file) {
      alert("Please choose an audio file first.");
      return;
    }

    setLoading(true);

    const formData = new FormData();
    formData.append("file", file);


    try {

      const response = await fetch(
        `${API_BASE_URL}/analyze`,
        {
          method: "POST",
          body: formData,
        }
      );


      console.log(response.status);

      const text = await response.text();

      console.log(text);

      const data = JSON.parse(text);

      setResult(data);

    } catch (error) {

      console.error(error);
      alert("Failed to analyze audio.");

    }


    setLoading(false);

  };


  return (

    <div className="app-shell">

      <aside className="sidebar">

        <div className="sidebar-brand">
          <div>
            <h1>Resonanca</h1>
            <p>Intelligent Music Analysis for DJs</p>
          </div>
        </div>


        <nav className="sidebar-nav" aria-label="Workspace sections">
          {sidebarItems.map(([icon, label]) => (
            <button
              type="button"
              className={`sidebar-item ${activeView === label ? "active" : ""}`}
              key={label}
              onClick={() => {
                if (
                  label === "Analyze Track"
                  || label === "Library"
                  || label === "Playlists"
                ) {
                  setActiveView(label);
                }
              }}
              disabled={
                label !== "Analyze Track"
                && label !== "Library"
                && label !== "Playlists"
              }
            >
              <span aria-hidden="true">{icon}</span>
              {label}
            </button>
          ))}
        </nav>


        <div className="tip-card">
          <span className="tip-icon" aria-hidden="true">
            ☼
          </span>
          <h2>Tip</h2>
          <p>
            Upload a track to get key, BPM, waveform,
            spectrogram and more insights.
          </p>
          <span className="tip-note" aria-hidden="true">
            ♫
          </span>
        </div>

      </aside>


      <main className="workspace">

        {activeView === "Playlists" ? (
          <PlaylistPage
            apiBaseUrl={API_BASE_URL}
            playlists={playlists}
            loading={playlistsLoading}
            error={playlistsError}
            onRefresh={loadPlaylists}
            onConnectSpotify={connectSpotify}
          />
        ) : activeView === "Library" ? (
          <>
            <header className="workspace-header library-header">
              <div>
                <h2>My Library</h2>
                <p>Browse tracks saved from your connected music sources.</p>
              </div>

              <div className="library-actions">
                <button
                  className="secondary-button"
                  onClick={connectSpotify}
                >
                  Connect Spotify
                </button>
                <button
                  className="analyze-button"
                  onClick={importSpotifyLibrary}
                  disabled={importing}
                >
                  {importing ? "Importing..." : "Import Spotify Library"}
                </button>
              </div>
            </header>

            <section className="library-panel">
              <header className="panel-header">
                <h2>Tracks</h2>
                <span>
                  {libraryTracks.length}{" "}
                  {libraryTracks.length === 1 ? "track" : "tracks"}
                </span>
              </header>

              <SpotifyPlayer
                ref={spotifyPlayerRef}
                track={selectedTrack}
                onPlaybackChange={setPlayingTrackId}
                onReadyChange={setSpotifyPlayerReady}
              />

              {playlistTrackTarget && (
                <div className="playlist-picker">
                  <div>
                    <strong>Add “{playlistTrackTarget.title}”</strong>
                    <span>Choose a DJ playlist.</span>
                  </div>
                  <select
                    value={targetPlaylistId}
                    onChange={(event) =>
                      setTargetPlaylistId(event.target.value)
                    }
                  >
                    <option value="">Select playlist</option>
                    {playlists.map((playlist) => (
                      <option value={playlist.id} key={playlist.id}>
                        {playlist.name}
                      </option>
                    ))}
                  </select>
                  <button
                    className="analyze-button"
                    onClick={addTrackToPlaylist}
                    disabled={!targetPlaylistId || addingToPlaylist}
                  >
                    {addingToPlaylist ? "Adding..." : "Add"}
                  </button>
                  <button
                    className="picker-cancel"
                    onClick={() => setPlaylistTrackTarget(null)}
                  >
                    Cancel
                  </button>
                </div>
              )}

              {libraryError && (
                <div className="library-message error-message">
                  {libraryError}
                </div>
              )}

              {libraryLoading ? (
                <div className="library-message">
                  Loading your library...
                </div>
              ) : libraryTracks.length === 0 ? (
                <div className="library-empty">
                  <span aria-hidden="true">♫</span>
                  <h3>Your library is empty</h3>
                  <p>
                    Connect Spotify, then import your saved tracks.
                  </p>
                </div>
              ) : (
                <div className="library-list">
                  <div className="library-list-header" aria-hidden="true">
                    <span>Track</span>
                    <span>Album</span>
                    <span>Duration</span>
                    <span>Add</span>
                  </div>

                  {libraryTracks.map((track) => (
                    <article
                      className={`library-track-row ${
                        selectedTrack?.id === track.id ? "selected" : ""
                      }`}
                      key={track.id}
                    >
                      {track.spotify_id ? (
                        <button
                          type="button"
                          className="track-play-button"
                          onClick={() => toggleLibraryTrack(track)}
                          disabled={!spotifyPlayerReady}
                          aria-label={
                            !spotifyPlayerReady
                              ? "Spotify player is loading"
                              : playingTrackId === track.spotify_id
                              ? `Stop ${track.title}`
                              : `Play ${track.title}`
                          }
                          title={
                            !spotifyPlayerReady
                              ? "Spotify player is loading"
                              : playingTrackId === track.spotify_id
                              ? "Stop"
                              : "Play in Resonanca"
                          }
                        >
                          {playingTrackId === track.spotify_id ? "■" : "▶"}
                        </button>
                      ) : (
                        <span
                          className="track-play-button disabled"
                          aria-hidden="true"
                        >
                          ▶
                        </span>
                      )}

                      {track.cover_image ? (
                        <img
                          src={track.cover_image}
                          alt=""
                          className="library-cover"
                        />
                      ) : (
                        <div className="library-cover cover-placeholder">
                          ♫
                        </div>
                      )}

                      <div className="library-track-info">
                        <strong title={track.title}>{track.title}</strong>
                        <span>{track.artist || "Unknown artist"}</span>
                        {selectedTrack?.id === track.id && (
                          <PlaybackWave
                            playing={
                              playingTrackId === track.spotify_id
                            }
                          />
                        )}
                      </div>

                      <span className="library-album">
                        {track.album || "Unknown album"}
                      </span>

                      <span className="library-duration">
                        {formatTrackDuration(track.duration)}
                      </span>

                      <button
                        type="button"
                        className="track-add-button"
                        onClick={() => {
                          setPlaylistTrackTarget(track);
                          setTargetPlaylistId("");
                        }}
                        disabled={!track.spotify_id}
                        aria-label={`Add ${track.title} to playlist`}
                        title="Add to playlist"
                      >
                        +
                      </button>
                    </article>
                  ))}
                </div>
              )}

            </section>
          </>
        ) : (
          <>
        <header className="workspace-header">
          <div>
            <h2>Analyze Track</h2>
            <p>Upload an audio file and get AI-powered music analysis.</p>
          </div>

          <button
            className="analyze-button"
            onClick={analyzeAudio}
          >
            {loading ? "Analyzing..." : "Analyze"}
          </button>
        </header>


        <section className="upload-panel">

          <label className="upload-dropzone">
            <input
              type="file"
              accept="audio/*"
              onChange={(e) =>
                setFile(e.target.files[0])
              }
            />

            <span className="upload-cloud" aria-hidden="true">
              ☁
            </span>
            <strong>Drag &amp; drop an audio file here</strong>
            <span>or click to browse</span>
            <small>MP3, WAV, FLAC, M4A</small>
          </label>


          <div className={`track-preview ${file ? "has-file" : ""}`}>
            <span className="track-art" aria-hidden="true">
              ♫
            </span>
            <div className="track-details">
              <strong>{file ? file.name : "No track selected"}</strong>
              <span>
                {file
                  ? result
                    ? `${result.duration.toFixed(2)} seconds`
                    : "Ready to analyze"
                  : "Choose a file to begin"
                }
              </span>
            </div>
            <span className="track-status">
              {result ? "Analyzed" : file ? "Selected" : "Waiting"}
            </span>
          </div>

        </section>


        <section className="analysis-panel">

          <header className="panel-header">
            <h2>Analysis Result</h2>
            <span>{result ? "Analysis complete" : "Awaiting track"}</span>
          </header>


          <div className="metrics-grid">

            <article className="metric-card">
              <div>
                <p>Duration</p>
                <strong>
                  {result
                    ? result.duration.toFixed(2) + " s"
                    : "—"
                  }
                </strong>
              </div>
            </article>


            <article className="metric-card">
              <div>
                <p>Sample Rate</p>
                <strong>
                  {result
                    ? result.sample_rate + " Hz"
                    : "—"
                  }
                </strong>
              </div>
            </article>


            <article className="metric-card">
              <div>
                <p>BPM</p>
                <strong>
                  {Number.isFinite(result?.bpm)
                    ? result.bpm.toFixed(1)
                    : "—"
                  }
                </strong>
              </div>
            </article>


            <article className="metric-card">
              <div>
                <p>Key</p>
                <strong>
                  {result?.key?.key && result?.key?.mode
                    ? `${result.key.key} ${result.key.mode}`
                    : "—"
                  }
                </strong>
              </div>
            </article>

          </div>


          <div className="visualization-grid">

            <article className="visual-card">
              <header>
                <div>
                  <span className="visual-icon" aria-hidden="true">≋</span>
                  <h2>Waveform</h2>
                </div>
                <span>Amplitude over time</span>
              </header>

              {result ? (
                <Waveform
                  samples={result.waveform}
                  duration={result.duration}
                />
              ) : (
                <div className="visual-empty">
                  Upload and analyze a track to view its waveform.
                </div>
              )}
            </article>


            <article className="visual-card">
              <header>
                <div>
                  <span className="visual-icon visual-icon-pink" aria-hidden="true">
                    ▦
                  </span>
                  <h2>Spectrogram</h2>
                </div>
                <span>Frequency over time</span>
              </header>

              {result ? (
                <Spectrogram
                  spectrogram={result.spectrogram}
                  duration={result.duration}
                />
              ) : (
                <div className="visual-empty">
                  Upload and analyze a track to view its spectrogram.
                </div>
              )}
            </article>

          </div>

        </section>
          </>
        )}

      </main>

    </div>

  );

}


export default App;
