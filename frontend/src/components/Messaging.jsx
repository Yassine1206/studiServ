// frontend/src/components/Messaging.jsx
// Messagerie temps réel WebSocket — StudiServ

import { useState, useEffect, useRef, useCallback } from 'react';
import apiClient from '../api/axios';

const API_BASE = import.meta.env.VITE_API_URL?.replace('/api', '') || 'http://localhost:8000';
const WS_BASE  = API_BASE.replace('http', 'ws');

// ── Helpers ───────────────────────────────────────────────────────────────────
function formatTime(iso) {
  if (!iso) return '';
  return new Date(iso).toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' });
}
function formatDate(iso) {
  if (!iso) return '';
  const d = new Date(iso);
  const today = new Date();
  if (d.toDateString() === today.toDateString()) return "Aujourd'hui";
  const yesterday = new Date(today); yesterday.setDate(today.getDate() - 1);
  if (d.toDateString() === yesterday.toDateString()) return 'Hier';
  return d.toLocaleDateString('fr-FR', { day: '2-digit', month: 'short' });
}
function Avatar({ name, size = 36 }) {
  const initials = (name || '?').split(' ').map(w => w[0]).join('').slice(0, 2).toUpperCase();
  const colors = ['#6C63FF','#3ECFCF','#FF6B6B','#FFB347','#56C596','#FF8DA1'];
  const color  = colors[(name || '').charCodeAt(0) % colors.length];
  return (
    <div style={{
      width: size, height: size, borderRadius: '50%',
      background: color, color: '#fff',
      display: 'flex', alignItems: 'center', justifyContent: 'center',
      fontSize: size * 0.38, fontWeight: 700, flexShrink: 0, userSelect: 'none',
    }}>{initials}</div>
  );
}

// ── Composant principal ───────────────────────────────────────────────────────
export default function Messaging({ currentUserId }) {
  const [conversations, setConversations] = useState([]);
  const [activeConv,    setActiveConv]    = useState(null);
  const [messages,      setMessages]      = useState([]);
  const [input,         setInput]         = useState('');
  const [loading,       setLoading]       = useState(true);
  const [sending,       setSending]       = useState(false);
  const [wsStatus,      setWsStatus]      = useState('disconnected'); // connected|disconnected|error
  const [typing,        setTyping]        = useState(false);
  const [typingUser,    setTypingUser]    = useState('');
  const [newConvModal,  setNewConvModal]  = useState(false);
  const [recipientId,   setRecipientId]   = useState('');

  const wsRef          = useRef(null);
  const messagesEndRef = useRef(null);
  const typingTimer    = useRef(null);
  const inputRef       = useRef(null);

  // ── Charger conversations ──────────────────────────────────────────────────
  useEffect(() => {
    loadConversations();
  }, []);

  const loadConversations = async () => {
    setLoading(true);
    try {
      const res = await apiClient.get('/messaging/conversations/');
      const data = Array.isArray(res.data) ? res.data : res.data.results || [];
      setConversations(data);
    } catch (e) {
      console.error('Erreur chargement conversations:', e);
      setConversations([]);
    } finally {
      setLoading(false);
    }
  };

  // ── Ouvrir une conversation ────────────────────────────────────────────────
  const openConversation = useCallback(async (conv) => {
    // Fermer l'ancien WebSocket
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    setActiveConv(conv);
    setMessages([]);
    setInput('');

    // Charger messages REST
    try {
      const res = await apiClient.get(`/messaging/conversations/${conv.id}/messages/`);
      const data = Array.isArray(res.data) ? res.data : res.data.results || [];
      setMessages(data);
    } catch (e) {
      console.error('Erreur chargement messages:', e);
    }

    // Connecter WebSocket
    connectWebSocket(conv.id);
  }, []);

  // ── WebSocket ──────────────────────────────────────────────────────────────
  const connectWebSocket = (convId) => {
    const token = localStorage.getItem('token');
    const url   = `${WS_BASE}/ws/chat/${convId}/${token ? `?token=${token}` : ''}`;

    const ws = new WebSocket(url);
    wsRef.current = ws;

    ws.onopen = () => {
      setWsStatus('connected');
    };

    ws.onmessage = (e) => {
      const data = JSON.parse(e.data);

      if (data.type === 'history') {
        setMessages(data.messages || []);
      } else if (data.type === 'message') {
        setMessages(prev => {
          // Éviter les doublons
          if (prev.find(m => m.id === data.message.id)) return prev;
          return [...prev, data.message];
        });
        // Mettre à jour le dernier message dans la liste
        setConversations(prev => prev.map(c =>
          c.id === convId ? { ...c, last_message: data.message } : c
        ));
      } else if (data.type === 'typing') {
        if (data.user_id !== currentUserId) {
          setTypingUser(data.username);
          setTyping(data.is_typing);
        }
      } else if (data.type === 'read') {
        setMessages(prev => prev.map(m =>
          m.sender_id !== currentUserId ? { ...m, is_read: true } : m
        ));
      }
    };

    ws.onerror = () => setWsStatus('error');
    ws.onclose = () => setWsStatus('disconnected');
  };

  // ── Scroll automatique ─────────────────────────────────────────────────────
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, typing]);

  // ── Envoyer message ────────────────────────────────────────────────────────
  const sendMessage = () => {
    const text = input.trim();
    if (!text || !wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) return;

    wsRef.current.send(JSON.stringify({ type: 'text', content: text }));
    setInput('');
    setSending(false);

    // Arrêter indicateur de frappe
    clearTimeout(typingTimer.current);
    wsRef.current.send(JSON.stringify({ type: 'typing', is_typing: false }));
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const handleInputChange = (e) => {
    setInput(e.target.value);

    // Indicateur de frappe
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: 'typing', is_typing: true }));
      clearTimeout(typingTimer.current);
      typingTimer.current = setTimeout(() => {
        if (wsRef.current?.readyState === WebSocket.OPEN) {
          wsRef.current.send(JSON.stringify({ type: 'typing', is_typing: false }));
        }
      }, 2000);
    }
  };

  // ── Upload fichier ─────────────────────────────────────────────────────────
  const handleFileUpload = async (e) => {
    const file = e.target.files[0];
    if (!file || !activeConv) return;

    const form = new FormData();
    form.append('file', file);
    form.append('message_type', file.type.startsWith('image/') ? 'image' : 'file');

    try {
      await apiClient.post(`/messaging/conversations/${activeConv.id}/upload/`, form, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      // Le message arrivera via WebSocket
    } catch (e) {
      console.error('Erreur upload:', e);
    }
  };

  // ── Nouvelle conversation ──────────────────────────────────────────────────
  const createConversation = async () => {
    if (!recipientId) return;
    try {
      const res = await apiClient.post('/messaging/conversations/create/', {
        recipient_id: parseInt(recipientId)
      });
      const conv = res.data;
      setConversations(prev => {
        if (prev.find(c => c.id === conv.id)) return prev;
        return [conv, ...prev];
      });
      setNewConvModal(false);
      setRecipientId('');
      openConversation(conv);
    } catch (e) {
      alert('Impossible de créer la conversation. Vérifiez l\'ID utilisateur.');
    }
  };

  // ── Cleanup ────────────────────────────────────────────────────────────────
  useEffect(() => {
    return () => {
      wsRef.current?.close();
      clearTimeout(typingTimer.current);
    };
  }, []);

  // ── Render ─────────────────────────────────────────────────────────────────
  return (
    <div style={styles.container}>

      {/* ── Liste des conversations ── */}
      <div style={styles.sidebar}>
        <div style={styles.sidebarHeader}>
          <span style={styles.sidebarTitle}>Messages</span>
          <button style={styles.newBtn} onClick={() => setNewConvModal(true)} title="Nouvelle conversation">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
          </button>
        </div>

        {loading ? (
          <div style={styles.emptyState}>Chargement...</div>
        ) : conversations.length === 0 ? (
          <div style={styles.emptyState}>
            <div style={{ fontSize: 32, marginBottom: 8 }}>💬</div>
            <div>Aucune conversation</div>
            <button style={styles.startBtn} onClick={() => setNewConvModal(true)}>
              Démarrer une conversation
            </button>
          </div>
        ) : (
          <div style={styles.convList}>
            {conversations.map(conv => {
              const other = conv.other_participant;
              const isActive = activeConv?.id === conv.id;
              const unread = conv.unread_count || 0;
              return (
                <div
                  key={conv.id}
                  style={{ ...styles.convItem, ...(isActive ? styles.convItemActive : {}) }}
                  onClick={() => openConversation(conv)}
                >
                  <Avatar name={other?.full_name || 'Utilisateur'} size={42} />
                  <div style={styles.convInfo}>
                    <div style={styles.convTop}>
                      <span style={styles.convName}>{other?.full_name || 'Utilisateur'}</span>
                      <span style={styles.convTime}>
                        {conv.last_message ? formatTime(conv.last_message.created_at) : ''}
                      </span>
                    </div>
                    <div style={styles.convBottom}>
                      <span style={styles.convPreview}>
                        {conv.last_message?.content || 'Démarrer la conversation...'}
                      </span>
                      {unread > 0 && <span style={styles.unreadBadge}>{unread}</span>}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* ── Zone de chat ── */}
      <div style={styles.chatArea}>
        {!activeConv ? (
          <div style={styles.noChatSelected}>
            <div style={{ fontSize: 48, marginBottom: 12 }}>💬</div>
            <div style={{ fontSize: 16, color: '#64748b' }}>Sélectionne une conversation</div>
          </div>
        ) : (
          <>
            {/* Header chat */}
            <div style={styles.chatHeader}>
              <Avatar name={activeConv.other_participant?.full_name || 'Utilisateur'} size={38} />
              <div style={{ marginLeft: 10 }}>
                <div style={styles.chatHeaderName}>
                  {activeConv.other_participant?.full_name || 'Utilisateur'}
                </div>
                <div style={{ fontSize: 12, color: wsStatus === 'connected' ? '#22c55e' : '#94a3b8' }}>
                  {wsStatus === 'connected' ? '● En ligne' : wsStatus === 'error' ? '● Erreur connexion' : '● Hors ligne'}
                </div>
              </div>
            </div>

            {/* Messages */}
            <div style={styles.messageList}>
              {messages.length === 0 && (
                <div style={{ textAlign: 'center', color: '#94a3b8', padding: '2rem', fontSize: 14 }}>
                  Démarrez la conversation !
                </div>
              )}

              {messages.map((msg, i) => {
                const isMe = msg.sender_id === currentUserId;
                const showDate = i === 0 || formatDate(messages[i-1]?.created_at) !== formatDate(msg.created_at);
                return (
                  <div key={msg.id || i}>
                    {showDate && (
                      <div style={styles.dateDivider}>
                        <span style={styles.dateDividerText}>{formatDate(msg.created_at)}</span>
                      </div>
                    )}
                    <div style={{ ...styles.messageRow, justifyContent: isMe ? 'flex-end' : 'flex-start' }}>
                      {!isMe && <Avatar name={msg.sender_name} size={28} />}
                      <div style={{ maxWidth: '68%', marginLeft: isMe ? 0 : 8, marginRight: isMe ? 0 : 0 }}>
                        {msg.message_type === 'image' && msg.file_url ? (
                          <img src={`${API_BASE}${msg.file_url}`} alt="Image" style={styles.imageMsg} />
                        ) : msg.message_type === 'file' && msg.file_url ? (
                          <a href={`${API_BASE}${msg.file_url}`} target="_blank" rel="noopener noreferrer" style={styles.fileMsg}>
                            📎 {msg.file_url.split('/').pop()}
                          </a>
                        ) : (
                          <div style={{ ...styles.bubble, ...(isMe ? styles.bubbleMe : styles.bubbleThem) }}>
                            {msg.content}
                          </div>
                        )}
                        <div style={{ ...styles.msgMeta, textAlign: isMe ? 'right' : 'left' }}>
                          {formatTime(msg.created_at)}
                          {isMe && <span style={{ marginLeft: 4 }}>{msg.is_read ? '✓✓' : '✓'}</span>}
                        </div>
                      </div>
                    </div>
                  </div>
                );
              })}

              {/* Indicateur de frappe */}
              {typing && (
                <div style={{ ...styles.messageRow, justifyContent: 'flex-start' }}>
                  <div style={styles.typingIndicator}>
                    <span style={styles.typingDot} />
                    <span style={{ ...styles.typingDot, animationDelay: '0.2s' }} />
                    <span style={{ ...styles.typingDot, animationDelay: '0.4s' }} />
                  </div>
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>

            {/* Input */}
            <div style={styles.inputArea}>
              <label style={styles.attachBtn} title="Envoyer un fichier">
                <input type="file" style={{ display: 'none' }} onChange={handleFileUpload} accept="image/*,.pdf" />
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#64748b" strokeWidth="2" strokeLinecap="round">
                  <path d="M21.44 11.05l-9.19 9.19a6 6 0 01-8.49-8.49l9.19-9.19a4 4 0 015.66 5.66l-9.2 9.19a2 2 0 01-2.83-2.83l8.49-8.48"/>
                </svg>
              </label>
              <textarea
                ref={inputRef}
                style={styles.input}
                value={input}
                onChange={handleInputChange}
                onKeyDown={handleKeyDown}
                placeholder="Écrire un message..."
                rows={1}
              />
              <button
                style={{ ...styles.sendBtn, opacity: input.trim() ? 1 : 0.4 }}
                onClick={sendMessage}
                disabled={!input.trim()}
              >
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#fff" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                  <line x1="22" y1="2" x2="11" y2="13"/>
                  <polygon points="22 2 15 22 11 13 2 9 22 2"/>
                </svg>
              </button>
            </div>
          </>
        )}
      </div>

      {/* ── Modal nouvelle conversation ── */}
      {newConvModal && (
        <div style={styles.modalOverlay} onClick={() => setNewConvModal(false)}>
          <div style={styles.modal} onClick={e => e.stopPropagation()}>
            <h3 style={{ margin: '0 0 16px', fontSize: 16 }}>Nouvelle conversation</h3>
            <input
              type="number"
              placeholder="ID de l'utilisateur"
              value={recipientId}
              onChange={e => setRecipientId(e.target.value)}
              style={styles.modalInput}
              autoFocus
            />
            <div style={{ display: 'flex', gap: 8, marginTop: 12 }}>
              <button style={styles.modalCancelBtn} onClick={() => setNewConvModal(false)}>Annuler</button>
              <button style={styles.modalConfirmBtn} onClick={createConversation}>Démarrer</button>
            </div>
          </div>
        </div>
      )}

      <style>{`
        @keyframes typingBounce {
          0%, 80%, 100% { transform: scale(0.6); opacity: 0.4; }
          40% { transform: scale(1); opacity: 1; }
        }
      `}</style>
    </div>
  );
}

// ── Styles ────────────────────────────────────────────────────────────────────
const styles = {
  container: {
    display: 'flex',
    height: '520px',
    border: '1px solid #e2e8f0',
    borderRadius: '16px',
    overflow: 'hidden',
    background: '#fff',
    boxShadow: '0 4px 20px rgba(0,0,0,0.06)',
  },
  sidebar: {
    width: '280px',
    borderRight: '1px solid #f1f5f9',
    display: 'flex',
    flexDirection: 'column',
    background: '#fafafa',
    flexShrink: 0,
  },
  sidebarHeader: {
    padding: '16px',
    borderBottom: '1px solid #f1f5f9',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  sidebarTitle: {
    fontWeight: 700,
    fontSize: 15,
    color: '#1e293b',
  },
  newBtn: {
    width: 30, height: 30,
    borderRadius: '50%',
    border: 'none',
    background: '#6C63FF',
    color: '#fff',
    cursor: 'pointer',
    display: 'flex', alignItems: 'center', justifyContent: 'center',
  },
  convList: {
    overflowY: 'auto',
    flex: 1,
  },
  convItem: {
    display: 'flex',
    alignItems: 'center',
    gap: 10,
    padding: '12px 14px',
    cursor: 'pointer',
    borderBottom: '1px solid #f8fafc',
    transition: 'background 0.15s',
  },
  convItemActive: {
    background: '#ede9fe',
  },
  convInfo: { flex: 1, minWidth: 0 },
  convTop: { display: 'flex', justifyContent: 'space-between', alignItems: 'center' },
  convName: { fontWeight: 600, fontSize: 13, color: '#1e293b', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' },
  convTime: { fontSize: 11, color: '#94a3b8', flexShrink: 0, marginLeft: 6 },
  convBottom: { display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: 2 },
  convPreview: { fontSize: 12, color: '#64748b', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' },
  unreadBadge: {
    background: '#6C63FF', color: '#fff',
    borderRadius: '50%', width: 18, height: 18,
    display: 'flex', alignItems: 'center', justifyContent: 'center',
    fontSize: 10, fontWeight: 700, flexShrink: 0,
  },
  emptyState: {
    flex: 1, display: 'flex', flexDirection: 'column',
    alignItems: 'center', justifyContent: 'center',
    color: '#94a3b8', fontSize: 13, padding: '2rem', textAlign: 'center',
  },
  startBtn: {
    marginTop: 12, padding: '8px 16px',
    background: '#6C63FF', color: '#fff',
    border: 'none', borderRadius: 8, cursor: 'pointer', fontSize: 13,
  },
  chatArea: {
    flex: 1, display: 'flex', flexDirection: 'column', minWidth: 0,
  },
  noChatSelected: {
    flex: 1, display: 'flex', flexDirection: 'column',
    alignItems: 'center', justifyContent: 'center',
  },
  chatHeader: {
    padding: '12px 16px',
    borderBottom: '1px solid #f1f5f9',
    display: 'flex', alignItems: 'center',
    background: '#fff',
  },
  chatHeaderName: {
    fontWeight: 600, fontSize: 14, color: '#1e293b',
  },
  messageList: {
    flex: 1, overflowY: 'auto',
    padding: '16px', display: 'flex',
    flexDirection: 'column', gap: 4,
  },
  messageRow: {
    display: 'flex', alignItems: 'flex-end', gap: 4, marginBottom: 2,
  },
  bubble: {
    padding: '8px 12px',
    borderRadius: 14,
    fontSize: 14,
    lineHeight: 1.5,
    wordBreak: 'break-word',
  },
  bubbleMe: {
    background: '#6C63FF',
    color: '#fff',
    borderBottomRightRadius: 4,
  },
  bubbleThem: {
    background: '#f1f5f9',
    color: '#1e293b',
    borderBottomLeftRadius: 4,
  },
  msgMeta: {
    fontSize: 10, color: '#94a3b8', marginTop: 2, paddingLeft: 4, paddingRight: 4,
  },
  dateDivider: {
    display: 'flex', alignItems: 'center', justifyContent: 'center',
    margin: '12px 0',
  },
  dateDividerText: {
    background: '#f1f5f9', color: '#64748b',
    fontSize: 11, padding: '3px 10px', borderRadius: 20,
  },
  imageMsg: {
    maxWidth: '100%', maxHeight: 200,
    borderRadius: 10, display: 'block',
  },
  fileMsg: {
    display: 'inline-block',
    background: '#f1f5f9', color: '#6C63FF',
    padding: '8px 12px', borderRadius: 10,
    fontSize: 13, textDecoration: 'none',
  },
  typingIndicator: {
    background: '#f1f5f9', padding: '8px 14px',
    borderRadius: 14, display: 'flex', gap: 4, alignItems: 'center',
    marginLeft: 36,
  },
  typingDot: {
    display: 'inline-block',
    width: 6, height: 6, borderRadius: '50%',
    background: '#94a3b8',
    animation: 'typingBounce 1s infinite',
  },
  inputArea: {
    padding: '10px 14px',
    borderTop: '1px solid #f1f5f9',
    display: 'flex', alignItems: 'flex-end', gap: 8,
    background: '#fff',
  },
  attachBtn: {
    width: 36, height: 36, display: 'flex',
    alignItems: 'center', justifyContent: 'center',
    cursor: 'pointer', borderRadius: 8,
    flexShrink: 0,
  },
  input: {
    flex: 1, border: '1.5px solid #e2e8f0',
    borderRadius: 12, padding: '8px 12px',
    fontSize: 14, resize: 'none',
    fontFamily: 'inherit', lineHeight: 1.4,
    maxHeight: 80, outline: 'none',
    background: '#f8fafc',
  },
  sendBtn: {
    width: 36, height: 36,
    borderRadius: '50%',
    background: '#6C63FF',
    border: 'none', cursor: 'pointer',
    display: 'flex', alignItems: 'center', justifyContent: 'center',
    flexShrink: 0, transition: 'opacity 0.2s',
  },
  modalOverlay: {
    position: 'fixed', inset: 0,
    background: 'rgba(0,0,0,0.4)',
    display: 'flex', alignItems: 'center', justifyContent: 'center',
    zIndex: 9999,
  },
  modal: {
    background: '#fff', borderRadius: 16,
    padding: '24px', width: 320,
    boxShadow: '0 20px 60px rgba(0,0,0,0.2)',
  },
  modalInput: {
    width: '100%', border: '1.5px solid #e2e8f0',
    borderRadius: 10, padding: '10px 12px',
    fontSize: 14, outline: 'none',
    boxSizing: 'border-box',
  },
  modalCancelBtn: {
    flex: 1, padding: '9px',
    border: '1px solid #e2e8f0', borderRadius: 10,
    background: '#fff', cursor: 'pointer', fontSize: 14,
  },
  modalConfirmBtn: {
    flex: 1, padding: '9px',
    border: 'none', borderRadius: 10,
    background: '#6C63FF', color: '#fff',
    cursor: 'pointer', fontSize: 14, fontWeight: 600,
  },
};