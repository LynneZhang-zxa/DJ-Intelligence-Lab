import "./PlaybackWave.css";

const BAR_HEIGHTS = [
  35, 58, 78, 48, 88, 62, 42, 72, 95, 55,
  82, 45, 68, 90, 52, 75, 38, 65, 84, 48,
];

function PlaybackWave({ playing }) {
  return (
    <div
      className={`playback-wave ${playing ? "playing" : ""}`}
      aria-label={playing ? "Track is playing" : "Track is paused"}
    >
      {BAR_HEIGHTS.map((height, index) => (
        <span
          key={`${height}-${index}`}
          style={{
            "--bar-height": `${height}%`,
            "--bar-delay": `${(index % 6) * -90}ms`,
          }}
        />
      ))}
    </div>
  );
}

export default PlaybackWave;
