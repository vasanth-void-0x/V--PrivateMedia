import React, { useState } from 'react';
import { createRoot } from 'react-dom/client';
import { Search, Plus, Paperclip, Send, LockKeyhole, MoreHorizontal, Users, MessageCircle, FolderClosed } from 'lucide-react';
import './styles.css';

const chats = [
  { name: '$arun', preview: 'See you tonight.', time: '2m', online: true },
  { name: '$kavi', preview: 'Sent a file', time: '12m', online: false },
  { name: 'Dev Group', preview: '$arun: build is ready', time: '1h', group: true },
];

function App() {
  const [active, setActive] = useState(chats[0]);
  const [message, setMessage] = useState('');
  const [messages, setMessages] = useState([
    { id: 1, mine: false, text: 'Hey, private space is ready.' },
    { id: 2, mine: true, text: 'Perfect. Send the project file here.' },
    { id: 3, mine: false, text: 'Sure — only our chat can access it.' },
  ]);

  const send = () => {
    const value = message.trim();
    if (!value) return;
    setMessages((old) => [...old, { id: Date.now(), mine: true, text: value }]);
    setMessage('');
  };

  return (
    <main className="shell">
      <aside className="sidebar">
        <div className="brand"><div className="mark">V</div><div><strong>Private Media</strong><span>Private by design</span></div></div>
        <div className="search"><Search size={17}/><input placeholder="Search chats" /></div>
        <div className="section-title"><span>Messages</span><button aria-label="New chat"><Plus size={18}/></button></div>
        <div className="chat-list">
          {chats.map((chat) => <button key={chat.name} className={`chat-row ${active.name === chat.name ? 'active' : ''}`} onClick={() => setActive(chat)}>
            <div className="avatar">{chat.group ? <Users size={18}/> : chat.name.slice(1,2).toUpperCase()}</div>
            <div className="chat-copy"><div><strong>{chat.name}</strong><time>{chat.time}</time></div><p>{chat.preview}</p></div>
          </button>)}
        </div>
        <nav className="nav"><button className="selected"><MessageCircle size={18}/>Chats</button><button><Users size={18}/>Groups</button><button><FolderClosed size={18}/>Files</button></nav>
      </aside>

      <section className="conversation">
        <header><div className="avatar">{active.group ? <Users size={18}/> : active.name.slice(1,2).toUpperCase()}</div><div><strong>{active.name}</strong><span>{active.online ? '● Online' : active.group ? 'Private group' : 'Private chat'}</span></div><div className="header-actions"><LockKeyhole size={17}/><button><MoreHorizontal size={20}/></button></div></header>
        <div className="messages">
          <div className="privacy"><LockKeyhole size={16}/><span>This is a private conversation</span></div>
          {messages.map((item) => <div key={item.id} className={`bubble ${item.mine ? 'mine' : ''}`}><p>{item.text}</p><small>{item.mine ? 'Sent ✓' : active.name}</small></div>)}
        </div>
        <div className="composer"><button aria-label="Attach file"><Paperclip size={20}/></button><input value={message} onChange={(e) => setMessage(e.target.value)} onKeyDown={(e) => e.key === 'Enter' && send()} placeholder="Message privately..."/><button className="send" onClick={send} aria-label="Send"><Send size={19}/></button></div>
      </section>
    </main>
  );
}

createRoot(document.getElementById('root')).render(<App />);
