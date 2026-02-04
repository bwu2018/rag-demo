import React, { useState } from "react";
import axios from "axios";

export const ChatInterface: React.FC = () => {
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState<ChatResponse | null>(null);
  const [loading, setLoading] = useState(false);

  type Source = {
    content: string;
    title: string;
    url: string;
  };

  type ChatResponse = {
    answer: string;
    sources: Source[];
  };

  const askQuestion = async () => {
    setLoading(true);
    try {
      const response = await axios.post("http://localhost:8000/chat/ask", {
        question,
      });
      console.log(response.data);

      setAnswer(response.data);
    } catch (error) {
      console.error("Question failed:", error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="chat-interface">
      <div className="question-input">
        <textarea
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder="Ask a question about your documents..."
        />
        <button onClick={askQuestion} disabled={loading}>
          {loading ? "Thinking..." : "Ask"}
        </button>
      </div>

      {answer && (
        <div className="answer">
          <h3>Answer:</h3>
          <p>{answer.answer}</p>
          <h4>Sources:</h4>
          {answer.sources.map((source, idx) => (
            <div key={idx} className="source">
              [{idx + 1}] {source.url}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
