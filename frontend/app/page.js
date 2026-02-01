"use client";
import { useState } from "react";

export default function Home() {
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  async function submitIdea() {
    setLoading(true);
    setResult(null);

    const res = await fetch("http://localhost:8000/check", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        title,
        description,
        k: 5,
      }),
    });

    const data = await res.json();
    setResult(data);
    setLoading(false);
  }

  return (
    <main style={{ padding: 24, fontFamily: "sans-serif", maxWidth: 800 }}>
      <h1>Hackathon Idea Originality Checker</h1>

      <input
        placeholder="Idea title"
        value={title}
        onChange={(e) => setTitle(e.target.value)}
        style={{ width: "100%", padding: 8, marginBottom: 8 }}
      />

      <textarea
        placeholder="Idea description"
        value={description}
        onChange={(e) => setDescription(e.target.value)}
        rows={4}
        style={{ width: "100%", padding: 8, marginBottom: 8 }}
      />

      <button onClick={submitIdea} disabled={loading}>
        {loading ? "Checking..." : "Check originality"}
      </button>

      {result && (
        <div style={{ marginTop: 24 }}>
          <h2>
            Score: {result.score} ({result.label})
          </h2>

          <h3>Suggestions</h3>
          <ul>
            {result.suggestions.map((s, i) => (
              <li key={i}>{s}</li>
            ))}
          </ul>

          <h3>Closest projects</h3>
          <ul>
            {result.neighbors.map((n, i) => (
              <li key={i}>
                <strong>{n.title}</strong> — similarity{" "}
                {(n.similarity * 100).toFixed(1)}%
                <br />
                <a href={n.url} target="_blank">View repo</a>
              </li>
            ))}
          </ul>
        </div>
      )}
    </main>
  );
}