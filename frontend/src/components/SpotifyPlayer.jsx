import {
  forwardRef,
  useEffect,
  useImperativeHandle,
  useRef,
  useState,
} from "react";
import "./SpotifyPlayer.css";

const IFRAME_API_URL =
  "https://open.spotify.com/embed/iframe-api/v1";

function loadSpotifyIframeApi() {
  if (window.__resonancaSpotifyIframeApi) {
    return Promise.resolve(
      window.__resonancaSpotifyIframeApi
    );
  }

  if (window.__resonancaSpotifyIframePromise) {
    return window.__resonancaSpotifyIframePromise;
  }

  window.__resonancaSpotifyIframePromise = new Promise(
    (resolve) => {
      window.onSpotifyIframeApiReady = (iframeApi) => {
        window.__resonancaSpotifyIframeApi = iframeApi;
        resolve(iframeApi);
      };

      if (!document.querySelector(`script[src="${IFRAME_API_URL}"]`)) {
        const script = document.createElement("script");
        script.src = IFRAME_API_URL;
        script.async = true;
        document.body.appendChild(script);
      }
    }
  );

  return window.__resonancaSpotifyIframePromise;
}

const SpotifyPlayer = forwardRef(function SpotifyPlayer(
  { track, onPlaybackChange, onReadyChange },
  ref,
) {
  const embedElementRef = useRef(null);
  const controllerRef = useRef(null);
  const loadedTrackIdRef = useRef(null);
  const pendingTrackRef = useRef(null);
  const initialTrackIdRef = useRef(null);
  const playbackChangeRef = useRef(onPlaybackChange);
  const readyChangeRef = useRef(onReadyChange);
  const playbackStartedRef = useRef(false);
  const [ready, setReady] = useState(false);
  const hasTrack = Boolean(track?.spotify_id);

  if (hasTrack && initialTrackIdRef.current === null) {
    initialTrackIdRef.current = track.spotify_id;
  }

  useEffect(() => {
    playbackChangeRef.current = onPlaybackChange;
  }, [onPlaybackChange]);

  useEffect(() => {
    readyChangeRef.current = onReadyChange;
  }, [onReadyChange]);

  useImperativeHandle(ref, () => ({
    playTrack(nextTrack) {
      const controller = controllerRef.current;
      if (!nextTrack?.spotify_id) {
        return false;
      }

      if (!controller) {
        pendingTrackRef.current = nextTrack;
        return false;
      }

      if (loadedTrackIdRef.current !== nextTrack.spotify_id) {
        controller.loadEntity(
          `spotify:track:${nextTrack.spotify_id}`
        );
        loadedTrackIdRef.current = nextTrack.spotify_id;
      }

      playbackStartedRef.current = false;
      controller.play();
      return true;
    },
    pause() {
      if (!controllerRef.current) {
        return false;
      }

      controllerRef.current.pause();
      playbackStartedRef.current = false;
      playbackChangeRef.current?.(null);
      return true;
    },
  }), []);

  useEffect(() => {
    const initialTrackId = initialTrackIdRef.current;
    if (!initialTrackId || !embedElementRef.current) {
      return;
    }

    let disposed = false;

    loadSpotifyIframeApi().then((iframeApi) => {
      if (disposed || controllerRef.current) {
        return;
      }

      iframeApi.createController(
        embedElementRef.current,
        {
          width: "100%",
          height: 152,
          uri: `spotify:track:${initialTrackId}`,
        },
        (controller) => {
          if (disposed) {
            controller.destroy();
            return;
          }

          controllerRef.current = controller;
          loadedTrackIdRef.current = initialTrackId;
          controller.addListener(
            "playback_started",
            (event) => {
              const playingUri = event.data.playingURI;
              playbackStartedRef.current = true;
              playbackChangeRef.current?.(
                playingUri?.split(":").pop() || null
              );
            }
          );
          controller.addListener(
            "playback_update",
            (event) => {
              const {
                duration,
                isPaused,
                position,
              } = event.data;
              const reachedTrackEnd = (
                duration > 0
                && position >= duration - 500
              );

              if (
                playbackStartedRef.current
                && isPaused
                && reachedTrackEnd
              ) {
                playbackStartedRef.current = false;
                playbackChangeRef.current?.(null);
              }
            }
          );
          setReady(true);
          readyChangeRef.current?.(true);

          const pendingTrack = pendingTrackRef.current;
          if (pendingTrack) {
            if (pendingTrack.spotify_id !== initialTrackId) {
              controller.loadEntity(
                `spotify:track:${pendingTrack.spotify_id}`
              );
              loadedTrackIdRef.current = pendingTrack.spotify_id;
            }
            playbackStartedRef.current = false;
            controller.play();
            pendingTrackRef.current = null;
          }
        }
      );
    });

    return () => {
      disposed = true;
      controllerRef.current?.destroy();
      controllerRef.current = null;
      loadedTrackIdRef.current = null;
      initialTrackIdRef.current = null;
      playbackStartedRef.current = false;
      setReady(false);
      readyChangeRef.current?.(false);
    };
  }, [hasTrack]);

  useEffect(() => {
    if (!ready || !track?.spotify_id) {
      return;
    }

    if (loadedTrackIdRef.current !== track.spotify_id) {
      controllerRef.current.loadEntity(
        `spotify:track:${track.spotify_id}`
      );
      loadedTrackIdRef.current = track.spotify_id;
      controllerRef.current.play();
    }
  }, [ready, track?.spotify_id]);

  if (!track?.spotify_id) {
    return null;
  }

  return (
    <section className="spotify-player" aria-label="Spotify player">
      <div className="spotify-player-heading">
        <div>
          <span>{ready ? "Ready to play" : "Loading player"}</span>
          <strong>{track.title}</strong>
          <small>{track.artist || "Unknown artist"}</small>
        </div>
      </div>

      <div ref={embedElementRef} className="spotify-embed" />
    </section>
  );
});

export default SpotifyPlayer;
