// src/components/ChatbotWidget.jsx
// M9 — Widget chatbot flottant StudiServ
// Usage : <ChatbotWidget /> dans App.jsx

import { useState, useRef, useEffect, useCallback } from "react";

const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";

// Générer ou récupérer la session_key du chatbot
function getSessionKey() {
  let key = sessionStorage.getItem("chatbot_session");
  if (!key) {
    key = crypto.randomUUID();
    sessionStorage.setItem("chatbot_session", key);
  }
  return key;
}

function BotAvatar() {
  return (
    <div style={{
      width: 32, height: 32, borderRadius: "50%",
      background: "linear-gradient(135deg, #6C63FF, #3ECFCF)",
      display: "flex", alignItems: "center", justifyContent: "center",
      color: "#fff", fontSize: 14, fontWeight: 700, flexShrink: 0
    }}>S</div>
  );
}

function MessageBubble({ msg }) {
  const isUser = msg.role === "user";
  return (
    <div style={{
      display: "flex",
      flexDirection: isUser ? "row-reverse" : "row",
      alignItems: "flex-end",
      gap: 8,
      marginBottom: 12,
    }}>
      {!isUser && <BotAvatar />}
      <div style={{
        maxWidth: "75%",
        padding: "10px 14px",
        borderRadius: isUser ? "18px 18px 4px 18px" : "18px 18px 18px 4px",
        background: isUser ? "#6C63FF" : "#F0F0F5",
        color: isUser ? "#fff" : "#1a1a2e",
        fontSize: 14,
        lineHeight: 1.5,
        wordBreak: "break-word",
      }}>
        {msg.content}
        {msg.sources && msg.sources.length > 0 && (
          <div style={{
            marginTop: 8, paddingTop: 8,
            borderTop: isUser ? "1px solid rgba(255,255,255,0.3)" : "1px solid #ddd",
            fontSize: 11, opacity: 0.75,
          }}>
            📚 Sources : {msg.sources.map(s => s.title).join(", ")}
          </div>
        )}
      </div>
    </div>
  );
}

function TypingIndicator() {
  return (
    <div style={{ display: "flex", alignItems: "flex-end", gap: 8, marginBottom: 12 }}>
      <BotAvatar />
      <div style={{
        padding: "10px 14px",
        borderRadius: "18px 18px 18px 4px",
        background: "#F0F0F5",
        display: "flex", gap: 4, alignItems: "center",
      }}>
        {[0, 1, 2].map(i => (
          <div key={i} style={{
            width: 6, height: 6, borderRadius: "50%",
            background: "#6C63FF",
            animation: "bounce 1s infinite",
            animationDelay: `${i * 0.2}s`,
          }} />
        ))}
      </div>
    </div>
  );
}

export default function ChatbotWidget() {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState([
    {
      id: 0,
      role: "assistant",
      content: "Salut ! 👋 Je suis l'assistant StudiServ. Comment puis-je t'aider ?",
    }
  ]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [sessionKey] = useState(getSessionKey);
  const [unreadCount, setUnreadCount] = useState(0);
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  // Scroll auto en bas
  useEffect(() => {
    if (isOpen) {
      messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }
  }, [messages, isOpen]);

  // Focus input à l'ouverture
  useEffect(() => {
    if (isOpen) {
      setUnreadCount(0);
      setTimeout(() => inputRef.current?.focus(), 100);
    }
  }, [isOpen]);

  const sendMessage = useCallback(async () => {
    const text = input.trim();
    if (!text || isLoading) return;

    const userMsg = { id: Date.now(), role: "user", content: text };
    setMessages(prev => [...prev, userMsg]);
    setInput("");
    setIsLoading(true);

    try {
      const token = localStorage.getItem("access_token");
      const headers = { "Content-Type": "application/json" };
      if (token) headers["Authorization"] = `Bearer ${token}`;

      const res = await fetch(`${API_BASE}/api/chatbot/chat/`, {
        method: "POST",
        headers,
        body: JSON.stringify({ message: text, session_key: sessionKey }),
      });

      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();

      const botMsg = {
        id: Date.now() + 1,
        role: "assistant",
        content: data.answer,
        sources: data.sources || [],
        fallback: data.fallback,
      };
      setMessages(prev => [...prev, botMsg]);

      if (!isOpen) {
        setUnreadCount(c => c + 1);
      }
    } catch (err) {
      setMessages(prev => [...prev, {
        id: Date.now() + 1,
        role: "assistant",
        content: "Désolé, je rencontre un problème de connexion. Réessaie dans un instant.",
      }]);
    } finally {
      setIsLoading(false);
    }
  }, [input, isLoading, sessionKey, isOpen]);

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  // Suggestions rapides
  const SUGGESTIONS = [
    "Comment créer une annonce ?",
    "Comment passer une commande ?",
    "Comment fonctionne le paiement ?",
    "Comment obtenir le badge de confiance ?",
  ];

  const showSuggestions = messages.length === 1;

  return (
    <>
      <style>{`
        @keyframes bounce {
          0%, 80%, 100% { transform: scale(0.7); opacity: 0.5; }
          40% { transform: scale(1); opacity: 1; }
        }
        @keyframes slideUp {
          from { opacity: 0; transform: translateY(20px) scale(0.95); }
          to { opacity: 1; transform: translateY(0) scale(1); }
        }
        .chatbot-widget * { box-sizing: border-box; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; }
        .chatbot-widget button:hover { opacity: 0.9; }
        .chatbot-input:focus { outline: none; border-color: #6C63FF; }
        .suggestion-btn:hover { background: #6C63FF !important; color: #fff !important; border-color: #6C63FF !important; }
      `}</style>

      <div className="chatbot-widget" style={{ position: "fixed", bottom: 24, right: 24, zIndex: 9999 }}>

        {/* Fenêtre du chat */}
        {isOpen && (
          <div style={{
            position: "absolute", bottom: 72, right: 0,
            width: 360, maxHeight: 520,
            background: "#fff", borderRadius: 20,
            boxShadow: "0 8px 40px rgba(0,0,0,0.18)",
            display: "flex", flexDirection: "column",
            animation: "slideUp 0.2s ease",
            overflow: "hidden",
          }}>
            {/* Header */}
            <div style={{
              padding: "14px 18px",
              background: "linear-gradient(135deg, #6C63FF, #3ECFCF)",
              display: "flex", alignItems: "center", gap: 10,
            }}>
              <BotAvatar />
              <div style={{ flex: 1 }}>
                <div style={{ color: "#fff", fontWeight: 700, fontSize: 14 }}>Assistant StudiServ</div>
                <div style={{ color: "rgba(255,255,255,0.8)", fontSize: 11 }}>● En ligne</div>
              </div>
              <button
                onClick={() => setIsOpen(false)}
                style={{
                  background: "rgba(255,255,255,0.2)", border: "none",
                  borderRadius: "50%", width: 28, height: 28,
                  color: "#fff", cursor: "pointer", fontSize: 16,
                  display: "flex", alignItems: "center", justifyContent: "center",
                }}
              >×</button>
            </div>

            {/* Messages */}
            <div style={{
              flex: 1, overflowY: "auto", padding: "16px",
              background: "#FAFAFA", minHeight: 0,
            }}>
              {messages.map(msg => (
                <MessageBubble key={msg.id} msg={msg} />
              ))}
              {isLoading && <TypingIndicator />}

              {/* Suggestions rapides */}
              {showSuggestions && !isLoading && (
                <div style={{ marginTop: 8 }}>
                  <div style={{ fontSize: 11, color: "#999", marginBottom: 8 }}>Questions fréquentes :</div>
                  <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
                    {SUGGESTIONS.map(s => (
                      <button
                        key={s}
                        className="suggestion-btn"
                        onClick={() => { setInput(s); setTimeout(sendMessage, 0); }}
                        style={{
                          fontSize: 12, padding: "5px 10px",
                          border: "1px solid #6C63FF", borderRadius: 20,
                          background: "#fff", color: "#6C63FF",
                          cursor: "pointer", transition: "all 0.15s",
                        }}
                      >{s}</button>
                    ))}
                  </div>
                </div>
              )}

              <div ref={messagesEndRef} />
            </div>

            {/* Input */}
            <div style={{
              padding: "12px 16px",
              borderTop: "1px solid #eee",
              background: "#fff",
              display: "flex", gap: 8, alignItems: "flex-end",
            }}>
              <textarea
                ref={inputRef}
                className="chatbot-input"
                value={input}
                onChange={e => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Pose ta question..."
                rows={1}
                style={{
                  flex: 1, border: "1.5px solid #e0e0e0",
                  borderRadius: 12, padding: "8px 12px",
                  fontSize: 14, resize: "none",
                  fontFamily: "inherit", lineHeight: 1.4,
                  maxHeight: 80, overflowY: "auto",
                  transition: "border-color 0.2s",
                }}
              />
              <button
                onClick={sendMessage}
                disabled={!input.trim() || isLoading}
                style={{
                  width: 38, height: 38,
                  borderRadius: "50%",
                  background: input.trim() && !isLoading ? "#6C63FF" : "#e0e0e0",
                  border: "none", cursor: input.trim() ? "pointer" : "not-allowed",
                  display: "flex", alignItems: "center", justifyContent: "center",
                  transition: "background 0.2s", flexShrink: 0,
                }}
              >
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#fff" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                  <line x1="22" y1="2" x2="11" y2="13" />
                  <polygon points="22 2 15 22 11 13 2 9 22 2" />
                </svg>
              </button>
            </div>
          </div>
        )}

        {/* Bouton flottant */}
        <button
          onClick={() => setIsOpen(o => !o)}
          style={{
            width: 56, height: 56, borderRadius: "50%",
            background: "linear-gradient(135deg, #6C63FF, #3ECFCF)",
            border: "none", cursor: "pointer",
            boxShadow: "0 4px 20px rgba(108,99,255,0.4)",
            display: "flex", alignItems: "center", justifyContent: "center",
            transition: "transform 0.2s",
            transform: isOpen ? "rotate(45deg)" : "rotate(0deg)",
          }}
        >
          {isOpen ? (
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#fff" strokeWidth="2.5" strokeLinecap="round">
              <line x1="18" y1="6" x2="6" y2="18" /><line x1="6" y1="6" x2="18" y2="18" />
            </svg>
          ) : (
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#fff" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
            </svg>
          )}

          {/* Badge non lu */}
          {!isOpen && unreadCount > 0 && (
            <div style={{
              position: "absolute", top: -4, right: -4,
              width: 20, height: 20, borderRadius: "50%",
              background: "#FF4757", color: "#fff",
              fontSize: 11, fontWeight: 700,
              display: "flex", alignItems: "center", justifyContent: "center",
              border: "2px solid #fff",
            }}>{unreadCount}</div>
          )}
        </button>
      </div>
    </>
  );
}
