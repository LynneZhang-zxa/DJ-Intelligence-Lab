import { useState } from "react";
import "./App.css";
import Spectrogram from "./components/Spectrogram";
import Waveform from "./components/Waveform";

function App() {

  const [file, setFile] = useState(null);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);


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
        "http://127.0.0.1:8000/analyze",
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

    <div className="app">

      <h1>Resonanca</h1>

      <p>
        Intelligent Music Analysis for DJs
      </p>



      <div className="upload-box">

        <h2>
          Upload Track
        </h2>


        <input
          type="file"
          accept="audio/*"
          onChange={(e) =>
            setFile(e.target.files[0])
          }
        />


        {file && (
          <p>
            Selected: {file.name}
          </p>
        )}


        <button onClick={analyzeAudio}>

          {loading
            ? "Analyzing..."
            : "Analyze Track"
          }

        </button>


      </div>





      <div className="result-box">

        <h2>
          Analysis Result
        </h2>


        <p>
          Duration:
          {" "}
          {result
            ? result.duration.toFixed(2) + " seconds"
            : "-"
          }
        </p>


        <p>
          Sample Rate:
          {" "}
          {result
            ? result.sample_rate + " Hz"
            : "-"
          }
        </p>


        <p>
          BPM:
          {" "}
          {Number.isFinite(result?.bpm)
            ? result.bpm.toFixed(1)
            : "-"
          }
        </p>


        <p>
          Key:
          -
        </p>


      </div>





      <div className="visual-box">

        <h2>
          Visualization
        </h2>

        {result ? (
          <Waveform
            samples={result.waveform}
            duration={result.duration}
          />
        ) : (
          <p>
            Waveform:
            Coming soon
          </p>
        )}


        {result && (
          <Spectrogram
            spectrogram={result.spectrogram}
            duration={result.duration}
          />
        )}


      </div>


    </div>

  );

}


export default App;
