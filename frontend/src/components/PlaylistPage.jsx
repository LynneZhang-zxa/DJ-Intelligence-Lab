import { useState } from "react";
import "./PlaylistPage.css";

function PlaylistPage({
  apiBaseUrl,
  playlists,
  loading,
  error,
  onRefresh,
  onConnectSpotify,
}) {
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [creating, setCreating] = useState(false);
  const [formError, setFormError] = useState("");
  const [selectedPlaylist, setSelectedPlaylist] = useState(null);
  const [detailLoading, setDetailLoading] = useState(false);

  const createPlaylist = async (event) => {
    event.preventDefault();
    if (!name.trim()) {
      return;
    }

    setCreating(true);
    setFormError("");

    try {
      const response = await fetch(`${apiBaseUrl}/playlists`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name: name.trim(),
          description: description.trim() || null,
        }),
      });
      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.detail || "Could not create playlist.");
      }

      setName("");
      setDescription("");
      setSelectedPlaylist({ ...data, tracks: [] });
      await onRefresh();
    } catch (createError) {
      setFormError(createError.message);
    } finally {
      setCreating(false);
    }
  };

  const openPlaylist = async (playlistId) => {
    setDetailLoading(true);
    setFormError("");

    try {
      const response = await fetch(
        `${apiBaseUrl}/playlists/${playlistId}`
      );
      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.detail || "Could not load playlist.");
      }
      setSelectedPlaylist(data);
    } catch (detailError) {
      setFormError(detailError.message);
    } finally {
      setDetailLoading(false);
    }
  };

  return (
    <>
      <header className="workspace-header playlist-page-header">
        <div>
          <h2>My Playlists</h2>
          <p>Create DJ sets and synchronize them with Spotify.</p>
        </div>
        <button
          className="secondary-button"
          onClick={onConnectSpotify}
        >
          Reconnect Spotify
        </button>
      </header>

      <section className="playlist-create-panel">
        <div>
          <h2>Create DJ Playlist</h2>
          <p>New playlists are private in Spotify.</p>
        </div>

        <form onSubmit={createPlaylist}>
          <input
            value={name}
            onChange={(event) => setName(event.target.value)}
            placeholder="Playlist name"
            maxLength={100}
            required
          />
          <input
            value={description}
            onChange={(event) => setDescription(event.target.value)}
            placeholder="Description (optional)"
            maxLength={300}
          />
          <button
            className="analyze-button"
            disabled={creating}
          >
            {creating ? "Creating..." : "Create Playlist"}
          </button>
        </form>
      </section>

      {(error || formError) && (
        <div className="library-message error-message">
          {formError || error}
        </div>
      )}

      <section className="playlists-panel">
        <header className="panel-header">
          <h2>DJ Playlists</h2>
          <span>{playlists.length} playlists</span>
        </header>

        {loading ? (
          <div className="playlist-empty">Loading playlists...</div>
        ) : playlists.length === 0 ? (
          <div className="playlist-empty">
            Create your first DJ playlist above.
          </div>
        ) : (
          <div className="playlist-card-grid">
            {playlists.map((playlist) => (
              <button
                type="button"
                className={`playlist-card ${
                  selectedPlaylist?.id === playlist.id
                    ? "selected"
                    : ""
                }`}
                key={playlist.id}
                onClick={() => openPlaylist(playlist.id)}
              >
                <span className="playlist-card-art">♫</span>
                <strong>{playlist.name}</strong>
                <small>
                  {playlist.track_count}{" "}
                  {playlist.track_count === 1 ? "track" : "tracks"}
                </small>
              </button>
            ))}
          </div>
        )}
      </section>

      {selectedPlaylist && (
        <section className="playlist-detail-panel">
          <header className="panel-header">
            <div>
              <h2>{selectedPlaylist.name}</h2>
              <p>{selectedPlaylist.description}</p>
            </div>
            <span>{selectedPlaylist.track_count} tracks</span>
          </header>

          {detailLoading ? (
            <div className="playlist-empty">Loading tracks...</div>
          ) : selectedPlaylist.tracks?.length ? (
            <div className="playlist-detail-list">
              {selectedPlaylist.tracks.map((track, index) => (
                <article key={track.id}>
                  <span>{index + 1}</span>
                  {track.cover_image ? (
                    <img src={track.cover_image} alt="" />
                  ) : (
                    <div className="playlist-track-placeholder">♫</div>
                  )}
                  <div>
                    <strong>{track.title}</strong>
                    <small>{track.artist || "Unknown artist"}</small>
                  </div>
                </article>
              ))}
            </div>
          ) : (
            <div className="playlist-empty compact">
              Add tracks from your Library.
            </div>
          )}
        </section>
      )}
    </>
  );
}

export default PlaylistPage;
