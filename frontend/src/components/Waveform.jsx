import "./Waveform.css";

const VIEWBOX_WIDTH = 1000;
const VIEWBOX_HEIGHT = 240;
const VERTICAL_PADDING = 16;

function createEnvelopePath(samples) {
  const bucketCount = Math.floor(samples.length / 2);

  if (bucketCount === 0) {
    return "";
  }

  const numericSamples = samples
    .slice(0, bucketCount * 2)
    .map(Number)
    .filter(Number.isFinite);
  const peak = Math.max(...numericSamples.map(Math.abs), 1e-6);
  const centerY = VIEWBOX_HEIGHT / 2;
  const amplitudeHeight = centerY - VERTICAL_PADDING;
  const xForBucket = (index) =>
    bucketCount === 1
      ? VIEWBOX_WIDTH / 2
      : (index / (bucketCount - 1)) * VIEWBOX_WIDTH;
  const yForAmplitude = (amplitude) =>
    centerY - (amplitude / peak) * amplitudeHeight;

  const upperPoints = [];
  const lowerPoints = [];

  for (let index = 0; index < bucketCount; index += 1) {
    const maximum = Number(samples[index * 2]);
    const minimum = Number(samples[index * 2 + 1]);

    if (!Number.isFinite(maximum) || !Number.isFinite(minimum)) {
      continue;
    }

    const x = xForBucket(index);
    upperPoints.push(`${x},${yForAmplitude(maximum)}`);
    lowerPoints.push(`${x},${yForAmplitude(minimum)}`);
  }

  if (upperPoints.length === 0) {
    return "";
  }

  return `M ${upperPoints.join(" L ")} L ${lowerPoints.reverse().join(" L ")} Z`;
}

function formatTime(seconds) {
  if (!Number.isFinite(seconds) || seconds < 0) {
    return "0:00";
  }

  const wholeSeconds = Math.round(seconds);
  const minutes = Math.floor(wholeSeconds / 60);
  const remainingSeconds = wholeSeconds % 60;

  return `${minutes}:${remainingSeconds.toString().padStart(2, "0")}`;
}

function Waveform({ samples, duration }) {
  const path = Array.isArray(samples) ? createEnvelopePath(samples) : "";

  if (!path) {
    return <p className="waveform-empty">No waveform data available.</p>;
  }

  return (
    <figure className="waveform">
      <svg
        className="waveform-chart"
        viewBox={`0 0 ${VIEWBOX_WIDTH} ${VIEWBOX_HEIGHT}`}
        preserveAspectRatio="none"
        role="img"
        aria-label={`Audio amplitude envelope from 0:00 to ${formatTime(duration)}`}
      >
        <line
          className="waveform-center-line"
          x1="0"
          y1={VIEWBOX_HEIGHT / 2}
          x2={VIEWBOX_WIDTH}
          y2={VIEWBOX_HEIGHT / 2}
        />
        <path className="waveform-envelope" d={path} />
      </svg>

      <figcaption className="waveform-time-axis">
        <span>0:00</span>
        <span>{formatTime(duration)}</span>
      </figcaption>
    </figure>
  );
}

export default Waveform;
