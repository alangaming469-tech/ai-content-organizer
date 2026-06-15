const { createRoot } = ReactDOM;
const { useState } = React;

function App() {
  const [query, setQuery] = useState("");
  const [text, setText] = useState("");
  const [output, setOutput] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function handleSummarize() {
    setError("");
    setOutput("");
    setLoading(true);
    try {
      const res = await fetch("http://localhost:8000/api/v1/summarize", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text, query }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Summarization failed");
      setOutput(JSON.stringify(data, null, 2));
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div style={{ maxWidth: 900, margin: "40px auto", padding: 20 }}>
      <h1>AI Content Organizer</h1>
      <div>
        <label htmlFor="query">Query</label><br/>
        <textarea
          id="query"
          placeholder="e.g. Rangkum untuk eksekutif"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          rows={3}
          style={{ width: "100%" }}
        />
      </div>
      <div style={{ marginTop: 12 }}>
        <label htmlFor="document">Document</label><br/>
        <textarea
          id="document"
          placeholder="Paste document text here..."
          value={text}
          onChange={(e) => setText(e.target.value)}
          rows={10}
          style={{ width: "100%" }}
        />
      </div>
      <button
        disabled={loading}
        onClick={handleSummarize}
        style={{ marginTop: 12 }}
      >
        {loading ? "Summarizing..." : "Summarize"}
      </button>
      {error && <p style={{ color: "red", marginTop: 12 }}>{error}</p>}
      <div style={{ marginTop: 12 }}>
        <label htmlFor="output">Output</label><br/>
        <textarea
          id="output"
          readOnly
          value={output}
          placeholder="Hasil ringkasan akan muncul di sini..."
          rows={12}
          style={{ width: "100%" }}
        />
      </div>
    </div>
  );
}

createRoot(document.getElementById("root")).render(<App />);
