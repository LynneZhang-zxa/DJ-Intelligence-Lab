import { useEffect, useRef } from "react";
import "./Spectrogram.css";

const MIN_DB = -80;
const MAX_DB = 0;

const COLOR_STOPS = [
  { position: 0, color: [0, 0, 4] },
  { position: 0.25, color: [81, 18, 124] },
  { position: 0.5, color: [183, 55, 121] },
  { position: 0.75, color: [252, 137, 97] },
  { position: 1, color: [252, 253, 191] },
];

function interpolateColor(position) {
  const clampedPosition = Math.max(0, Math.min(1, position));
  const upperIndex = COLOR_STOPS.findIndex(
    (stop) => stop.position >= clampedPosition,
  );
  const upperStop = COLOR_STOPS[Math.max(upperIndex, 1)];
  const lowerStop = COLOR_STOPS[Math.max(upperIndex - 1, 0)];
  const range = upperStop.position - lowerStop.position;
  const amount = range === 0
    ? 0
    : (clampedPosition - lowerStop.position) / range;

  return lowerStop.color.map((channel, index) =>
    Math.round(
      channel + (upperStop.color[index] - channel) * amount,
    ),
  );
}

const COLOR_BY_DB = Array.from(
  { length: MAX_DB - MIN_DB + 1 },
  (_, index) => interpolateColor(index / (MAX_DB - MIN_DB)),
);

function colorForDb(value) {
  const db = Number.isFinite(Number(value)) ? Number(value) : MIN_DB;
  const index = Math.round(
    Math.max(MIN_DB, Math.min(MAX_DB, db)) - MIN_DB,
  );

  return COLOR_BY_DB[index];
}

function getMatrixDimensions(spectrogram) {
  const values = spectrogram?.values;

  if (
    spectrogram?.orientation !== "frequency_time"
    || !Array.isArray(values)
    || values.length === 0
    || !Array.isArray(values[0])
    || values[0].length === 0
  ) {
    return null;
  }

  const timeBins = values[0].length;
  const hasConsistentRows = values.every(
    (row) => Array.isArray(row) && row.length === timeBins,
  );

  if (!hasConsistentRows) {
    return null;
  }

  return {
    frequencyBins: values.length,
    timeBins,
  };
}

function Spectrogram({ spectrogram }) {
  const canvasRef = useRef(null);
  const dimensions = getMatrixDimensions(spectrogram);

  useEffect(() => {
    const canvas = canvasRef.current;

    if (!canvas || !dimensions) {
      return;
    }

    const { frequencyBins, timeBins } = dimensions;
    const context = canvas.getContext("2d");
    const imageData = context.createImageData(timeBins, frequencyBins);

    canvas.width = timeBins;
    canvas.height = frequencyBins;

    for (
      let frequencyIndex = 0;
      frequencyIndex < frequencyBins;
      frequencyIndex += 1
    ) {
      const canvasY = frequencyBins - 1 - frequencyIndex;

      for (let timeIndex = 0; timeIndex < timeBins; timeIndex += 1) {
        const pixelIndex = (
          canvasY * timeBins + timeIndex
        ) * 4;
        const color = colorForDb(
          spectrogram.values[frequencyIndex][timeIndex],
        );

        imageData.data[pixelIndex] = color[0];
        imageData.data[pixelIndex + 1] = color[1];
        imageData.data[pixelIndex + 2] = color[2];
        imageData.data[pixelIndex + 3] = 255;
      }
    }

    context.putImageData(imageData, 0, 0);
  }, [spectrogram, dimensions]);

  if (!dimensions) {
    return (
      <p className="spectrogram-empty">
        No spectrogram data available.
      </p>
    );
  }

  return (
    <figure className="spectrogram">
      <canvas
        ref={canvasRef}
        className="spectrogram-canvas"
        role="img"
        aria-label="Spectrogram showing frequency content over time"
      />
    </figure>
  );
}

export default Spectrogram;
