import React, { useState, useEffect } from 'react';
import { Send, Save, PlusCircle, Square, AlertCircle } from 'lucide-react';
import { Alert, AlertDescription, AlertTitle } from './ui/alert';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism';

const CodeBlock = ({ code }) => (
    <SyntaxHighlighter 
      language="ruby" 
      style={vscDarkPlus}
      customStyle={{
        backgroundColor: '#1E1E1E',
        padding: '1em',
        borderRadius: '0.5em',
        fontSize: '0.9em',
      }}
    >
      {code}
    </SyntaxHighlighter>
  );


    const ChatMessage = ({ message, isUser }) => {
    const parts = message.content.split(/(```[\s\S]*?```)/);
    
    return (
        <div className={`mb-4 ${isUser ? 'ml-auto' : 'mr-auto'} max-w-[80%]`}>
        <div className={`p-3 rounded-lg ${isUser ? 'bg-purple-600 text-white' : 'bg-gray-100 text-gray-800'}`}>
            {parts.map((part, index) => {
            if (part.startsWith('```') && part.endsWith('```')) {
                const code = part.slice(3, -3).trim();
                return <CodeBlock key={index} code={code} />;
            }
            return <p key={index}>{part}</p>;
            })}
        </div>
        </div>
    );
    };


const SonicPiChatUI = () => {
    const [chatHistory, setChatHistory] = useState([]);
    const [inputMessage, setInputMessage] = useState('');

    useEffect(() => {
        const fetchChatHistory = async () => {
        try {
            const response = await fetch(`${process.env.REACT_APP_API_URL}/api/chat-history`);
            const data = await response.json();
            setChatHistory(data);
        } catch (error) {
            console.error('Failed to fetch chat history:', error);
        }
        };

        fetchChatHistory();
    }, []);

    const handleSendMessage = async () => {
        if (inputMessage.trim() === '') return;

        try {
            const response = await fetch(`${process.env.REACT_APP_API_URL}/api/send-message`, {
            method: 'POST',
            body: JSON.stringify({ message: inputMessage }),
            headers: { 'Content-Type': 'application/json' },
            });
            const data = await response.json();

            setChatHistory(prev => [...prev, { content: inputMessage, isUser: true }, { content: data.response, isUser: false }]);
            setInputMessage('');
        } catch (error) {
            console.error('Failed to send message:', error);
        }
    };

    const handleNewChat = async () => {
        try {
          await fetch(`${process.env.REACT_APP_API_URL}/api/new-chat`, { method: 'POST' });
          setChatHistory([]);
        } catch (error) {
          console.error('Failed to start new chat:', error);
        }
      };
    
      const handleStopMusic = async () => {
        try {
          await fetch(`${process.env.REACT_APP_API_URL}/api/stop-music`, { method: 'POST' });
        } catch (error) {
          console.error('Failed to stop music:', error);
        }
      };

    const handleSave = async () => {
    try {
        const response = await fetch(`${process.env.REACT_APP_API_URL}/api/save-code`, { method: 'POST' });
        const data = await response.json();
        alert(data.message);
    } catch (error) {
        console.error('Failed to save code:', error);
        alert('Failed to save code. Please try again.');
    }
  };


  return (
    <div className="flex h-screen bg-gray-100">
      <div className="w-full max-w-4xl mx-auto flex flex-col bg-white shadow-xl">
        <header className="bg-purple-700 text-white p-4 flex justify-between items-center">
          <h1 className="text-2xl font-bold">Sonic Pi Controller</h1>
          <button
            onClick={handleStopMusic}
            className="p-2 bg-red-500 text-white rounded-md hover:bg-red-600 focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-offset-2 transition-colors duration-200"
            title="Stop the music"
          >
            <Square className="h-6 w-6" />
          </button>
        </header>
        <div className="flex-grow flex flex-col p-4 overflow-hidden">
          <div className="bg-yellow-100 border-l-4 border-yellow-500 text-yellow-700 p-4 mb-4 flex items-start">
            <AlertCircle className="h-5 w-5 mr-2 flex-shrink-0 mt-0.5" />
            <div>
              <p className="font-bold">Tip</p>
              <p>You can ask questions about music or Sonic Pi without changing the current music.</p>
            </div>
          </div>
          <div className="flex-grow overflow-y-auto mb-4 pr-4 space-y-4">
            {chatHistory.map((message, index) => (
              <ChatMessage key={index} message={message} isUser={message.isUser} />
            ))}
          </div>
          <div className="flex space-x-2">
          <input
            type="text"
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && handleSendMessage()}
            className="flex-grow p-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500"
            placeholder="Type your message..."
          />
          <button
            onClick={handleSendMessage}
            className="px-4 py-2 bg-purple-600 text-white rounded-md hover:bg-purple-700 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:ring-offset-2 transition-colors duration-200"
          >
            <Send className="h-5 w-5" />
          </button>
          <button
            onClick={handleSave}
            className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-green-500 focus:ring-offset-2 transition-colors duration-200"
          >
            <Save className="h-5 w-5" />
          </button>
          <button
            onClick={handleNewChat}
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 transition-colors duration-200"
            title="Start a new chat; existing music will not be stopped"
          >
            <PlusCircle className="h-5 w-5" />
          </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SonicPiChatUI;