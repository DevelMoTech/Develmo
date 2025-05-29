/* eslint-disable @next/next/no-img-element */
import { useState, useEffect } from "react";
import { useSession, signOut } from "next-auth/react";
import { useRouter } from "next/router";
import styles from "../styles/Chat.module.css";
import {
  FiMenu,
  FiX,
  FiPlus,
  FiSearch,
  FiMessageSquare,
  FiTrash2,
  FiUser,
  FiLogOut,
  FiCopy,
  FiRefreshCw,
  FiThumbsUp,
  FiThumbsDown,
  FiSettings,
} from "react-icons/fi";
import { BsRobot, BsMoon, BsSun } from "react-icons/bs";

export default function Chat() {
  const { data: session, status } = useSession();
  const router = useRouter();
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [activeChat, setActiveChat] = useState(null);
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [loading, setLoading] = useState(false);
  const [chatHistory, setChatHistory] = useState({});
  const [isNewChat, setIsNewChat] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");
  const [darkMode, setDarkMode] = useState(true);
  const [showLogoutDialog, setShowLogoutDialog] = useState(false);
  const [showClearDialog, setShowClearDialog] = useState(false);
  const [isAdmin, setIsAdmin] = useState(false);

  // Backend API URL
  const BACKEND_API_URL = "http://127.0.0.1:5010";

  // Redirect if not authenticated
  useEffect(() => {
    if (status === "unauthenticated") {
      router.push("/auth/login");
    }
  }, [status, router]);

  // Check admin role
  useEffect(() => {
    if (typeof window !== 'undefined') {
      const role = localStorage.getItem('userRole');
      setIsAdmin(role === 'admin');
    }
  }, []);

  // Fetch chat history
  useEffect(() => {
    if (status === "authenticated") {
      fetchChatHistory();
    }
  }, [status]);

  const fetchChatHistory = async () => {
    try {
      const response = await fetch("/api/chats");
      if (response.ok) {
        const data = await response.json();
        setChatHistory(data);
      }
    } catch (error) {
      console.error("Error fetching chat history:", error);
    }
  };

  // Fetch messages for active chat
  useEffect(() => {
    if (activeChat && !isNewChat) {
      fetchMessages(activeChat);
    }
  }, [activeChat, isNewChat]);

  const fetchMessages = async (chatId) => {
    try {
      const response = await fetch(`/api/chats/${chatId}`);
      if (response.ok) {
        const data = await response.json();
        setMessages(data.messages);
      }
    } catch (error) {
      console.error("Error fetching messages:", error);
    }
  };

  // Create a new chat
  const createNewChat = async () => {
    try {
      const response = await fetch("/api/chats", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          title: "New Chat",
          messages: [
            {
              text: "Hello! I'm your AI assistant. How can I help you today?",
              sender: "bot",
            },
          ],
          userId: session.user.id,
        }),
      });

      if (response.ok) {
        const data = await response.json();
        setActiveChat(data._id);
        setMessages(data.messages);
        setIsNewChat(false);
        await fetchChatHistory();
      }
    } catch (error) {
      console.error("Error creating new chat:", error);
    }
  };

  // Handle sending a message
  const handleSendMessage = async (e) => {
    e.preventDefault();
    if (!input.trim()) return;

    const newUserMessage = { text: input, sender: "user" };
    const updatedMessages = [...messages, newUserMessage];

    setMessages(updatedMessages);
    setInput("");
    setLoading(true);

    try {
      if (isNewChat) {
        await createNewChat();
      }

      await updateChat(updatedMessages);

      const botResponse = await getBotResponse(input);
      const newBotMessage = {
        text: botResponse.reply,
        sender: "bot",
        sources: botResponse.sources || [],
      };
      const finalMessages = [...updatedMessages, newBotMessage];

      setMessages(finalMessages);
      await updateChat(finalMessages);

      setLoading(false);
    } catch (error) {
      console.error("Error:", error);
      setMessages([
        ...updatedMessages,
        {
          text: "Sorry, I encountered an error processing your request.",
          sender: "bot",
        },
      ]);
      setLoading(false);
    }
  };

  const getBotResponse = async (userInput) => {
    try {
      const response = await fetch(`${BACKEND_API_URL}/chat/`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ message: userInput }),
      });

      if (!response.ok) {
        throw new Error(`API request failed with status ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error("Error getting bot response:", error);
      return {
        reply:
          "I'm sorry, I encountered an error processing your request. Please try again.",
        sources: [],
      };
    }
  };

  const updateChat = async (messages) => {
    if (!activeChat) return;

    try {
      await fetch(`/api/chats/${activeChat}`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          messages,
          title: messages[0]?.text || "New Chat",
        }),
      });

      await fetchChatHistory();
    } catch (error) {
      console.error("Error updating chat:", error);
      throw error;
    }
  };

  const handleSelectChat = (chatId) => {
    setActiveChat(chatId);
    setIsNewChat(false);
  };

  const handleNewChat = () => {
    setMessages([
      {
        text: "Hello! I'm your AI assistant. How can I help you today?",
        sender: "bot",
      },
    ]);
    setActiveChat(null);
    setIsNewChat(true);
    setInput("");
  };

  const handleClearConversations = async () => {
    try {
      await fetch("/api/chats", {
        method: "DELETE",
      });
      await fetchChatHistory();
      handleNewChat();
      setShowClearDialog(false);
    } catch (error) {
      console.error("Error clearing conversations:", error);
    }
  };

  const handleAdminClick = () => {
    router.push("/admin");
  };

  const filteredChatHistory = Object.entries(chatHistory).reduce(
    (acc, [date, chats]) => {
      const filteredChats = chats.filter((chat) =>
        chat.title.toLowerCase().includes(searchQuery.toLowerCase())
      );

      if (filteredChats.length > 0) {
        acc[date] = filteredChats;
      }

      return acc;
    },
    {}
  );

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    const today = new Date();
    const yesterday = new Date(today);
    yesterday.setDate(yesterday.getDate() - 1);

    if (date.toDateString() === today.toDateString()) {
      return "Today";
    } else if (date.toDateString() === yesterday.toDateString()) {
      return "Yesterday";
    } else {
      return date.toLocaleDateString("en-US", {
        month: "long",
        day: "numeric",
        year: "numeric",
      });
    }
  };

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text);
  };

  if (status !== "authenticated") {
    return <div className={styles.container}>Loading...</div>;
  }

  return (
    <div
      className={`${styles.container} ${darkMode ? styles.dark : styles.light}`}
    >
      {/* Sidebar */}
      <div className={`${styles.sidebar} ${sidebarOpen ? styles.open : ""}`}>
        {/* User info at the top */}
        <div className={styles.userInfo}>
          <div className={styles.userAvatar}>
            {session.user.image ? (
              <img src={session.user.image} alt={session.user.name} />
            ) : (
              <FiUser className={styles.icon} />
            )}
          </div>
          <div className={styles.userDetails}>
            <span className={styles.userName}>{session.user.name}</span>
          </div>
          <button
            className={styles.closeSidebarButton}
            onClick={() => setSidebarOpen(false)}
            aria-label="Close sidebar"
          >
            <FiX className={styles.icon} />
          </button>
        </div>

        <div className={styles.searchContainer}>
          <FiSearch className={styles.searchIcon} />
          <input
            type="text"
            placeholder="Search chats..."
            className={styles.searchInput}
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
        </div>

        <div className={styles.chatHistory}>
          {Object.entries(filteredChatHistory).map(([date, chats]) => (
            <div key={date} className={styles.dateSection}>
              <h3 className={styles.dateHeader}>{formatDate(date)}</h3>
              <ul>
                {chats.map((chat) => (
                  <li
                    key={chat.id}
                    className={`${styles.chatItem} ${
                      activeChat === chat.id ? styles.active : ""
                    }`}
                    onClick={() => handleSelectChat(chat.id)}
                  >
                    <FiMessageSquare className={styles.chatIcon} />
                    <div className={styles.chatInfo}>
                      <span className={styles.chatTitle}>{chat.title}</span>
                    </div>
                    <button
                      className={styles.deleteChatButton}
                      onClick={async (e) => {
                        e.stopPropagation();
                        try {
                          await fetch(`/api/chats/${chat.id}`, {
                            method: "DELETE",
                          });
                          await fetchChatHistory();
                          if (activeChat === chat.id) {
                            handleNewChat();
                          }
                        } catch (error) {
                          console.error("Error deleting chat:", error);
                        }
                      }}
                    >
                      <FiTrash2 className={styles.icon} />
                    </button>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        {/* New chat button at the bottom of chat list */}
        <button className={styles.newChatButton} onClick={handleNewChat}>
          <FiPlus className={styles.icon} />
          Start a new chat
        </button>

        {/* Bottom options */}
        <div className={styles.bottomOptions}>
          {isAdmin && (
            <button
              className={styles.optionButton}
              onClick={handleAdminClick}
            >
              <FiSettings className={styles.icon} />
              Admin Panel
            </button>
          )}
          <button
            className={styles.optionButton}
            onClick={() => setShowClearDialog(true)}
          >
            <FiTrash2 className={styles.icon} />
            Clear conversations
          </button>
          <button
            className={styles.optionButton}
            onClick={() => setShowLogoutDialog(true)}
          >
            <FiLogOut className={styles.icon} />
            Log out
          </button>
        </div>
      </div>

      {/* Main Chat Area */}
      <div className={styles.main}>
        {/* Top Bar */}
        <div className={styles.topBar}>
          {!sidebarOpen && (
            <button
              className={styles.menuButton}
              onClick={() => setSidebarOpen(true)}
              aria-label="Open sidebar"
            >
              <FiMenu className={styles.icon} />
            </button>
          )}
          <h2 className={styles.chatTitle}>
            {activeChat
              ? chatHistory[Object.keys(chatHistory)[0]]?.find(
                  (c) => c.id === activeChat
                )?.title || "Chat"
              : "New Chat"}
          </h2>
        </div>

        {/* Messages */}
        <div className={styles.messages}>
          {messages.length === 0 && !loading && (
            <div className={styles.welcomeMessage}>
              <div className={styles.welcomeLogo}>
                <img
                  className={styles.welcomeimage}
                  src="/images/devlmo.png"
                  alt={session.user.name}
                />
              </div>
              <div className={styles.examplePrompts}>
                <form
                  onSubmit={handleSendMessage}
                  className={styles.centeredInput}
                >
                  <div className={styles.inputContainer}>
                    <input
                      type="text"
                      value={input}
                      onChange={(e) => setInput(e.target.value)}
                      placeholder='Example : "Explain quantum computing in simple terms"'
                      className={styles.messageInput}
                      disabled={loading}
                    />
                    <button
                      type="submit"
                      className={styles.sendButton}
                      disabled={!input.trim() || loading}
                    >
                      <svg
                        width="20"
                        height="20"
                        viewBox="0 0 24 24"
                        fill="none"
                        xmlns="http://www.w3.org/2000/svg"
                      >
                        <path
                          d="M22 2L11 13M22 2L15 22L11 13M11 13L2 9"
                          stroke="currentColor"
                          strokeWidth="2"
                          strokeLinecap="round"
                          strokeLinejoin="round"
                        />
                      </svg>
                    </button>
                  </div>
                </form>
                <div className={styles.features}>
                  <div className={styles.featureItem}>
                    <div className={styles.featureIcon}>
                      <svg
                        width="24"
                        height="24"
                        viewBox="0 0 24 24"
                        fill="none"
                        xmlns="http://www.w3.org/2000/svg"
                      >
                        <path
                          d="M9 12L11 14L15 10M21 12C21 16.9706 16.9706 21 12 21C7.02944 21 3 16.9706 3 12C3 7.02944 7.02944 3 12 3C16.9706 3 21 7.02944 21 12Z"
                          stroke="#085A8C"
                          strokeWidth="2"
                          strokeLinecap="round"
                          strokeLinejoin="round"
                        />
                      </svg>
                    </div>
                    <h4>Clear and precise</h4>
                    <p>Pariatur sint laborum cillum aute consectetur irure.</p>
                  </div>
                  <div className={styles.featureItem}>
                    <div className={styles.featureIcon}>
                      <svg
                        width="24"
                        height="24"
                        viewBox="0 0 24 24"
                        fill="none"
                        xmlns="http://www.w3.org/2000/svg"
                      >
                        <path
                          d="M16 7C16 9.20914 14.2091 11 12 11C9.79086 11 8 9.20914 8 7C8 4.79086 9.79086 3 12 3C14.2091 3 16 4.79086 16 7Z"
                          stroke="#085A8C"
                          strokeWidth="2"
                          strokeLinecap="round"
                          strokeLinejoin="round"
                        />
                        <path
                          d="M12 14C8.13401 14 5 17.134 5 21H19C19 17.134 15.866 14 12 14Z"
                          stroke="#085A8C"
                          strokeWidth="2"
                          strokeLinecap="round"
                          strokeLinejoin="round"
                        />
                      </svg>
                    </div>
                    <h4>Personalized answers</h4>
                    <p>Pariatur sint laborum cillum aute consectetur irure.</p>
                  </div>
                  <div className={styles.featureItem}>
                    <div className={styles.featureIcon}>
                      <svg
                        width="24"
                        height="24"
                        viewBox="0 0 24 24"
                        fill="none"
                        xmlns="http://www.w3.org/2000/svg"
                      >
                        <path
                          d="M13 10V3L4 14H11L11 21L20 10H13Z"
                          stroke="#085A8C"
                          strokeWidth="2"
                          strokeLinecap="round"
                          strokeLinejoin="round"
                        />
                      </svg>
                    </div>
                    <h4>Increased efficiency</h4>
                    <p>Pariatur sint laborum cillum aute consectetur irure.</p>
                  </div>
                </div>
              </div>
            </div>
          )}

          {messages.map((message, index) => (
            <div
              key={index}
              className={`${styles.message} ${
                message.sender === "user"
                  ? styles.userMessage
                  : styles.botMessage
              }`}
            >
              {message.sender === "bot" && (
                <div className={styles.avatar}>
                  <BsRobot className={styles.botIcon} />
                </div>
              )}
              <div className={styles.messageContent}>
                <div className={styles.messageText}>{message.text}</div>
                {message.sources && message.sources.length > 0 && (
                  <div className={styles.sourcesContainer}>
                    <details className={styles.sourcesDropdown}>
                      <summary>Sources</summary>
                      <ul>
                        {message.sources.map((source, i) => (
                          <li key={i}>
                            <a
                              href={source}
                              target="_blank"
                              rel="noopener noreferrer"
                            >
                              {source}
                            </a>
                          </li>
                        ))}
                      </ul>
                    </details>
                  </div>
                )}
                {message.sender === "bot" && (
                  <div className={styles.messageActions}>
                    <button
                      className={styles.messageAction}
                      title="Copy"
                      onClick={() => copyToClipboard(message.text)}
                    >
                      <FiCopy />
                    </button>
                    <button className={styles.messageAction} title="Regenerate">
                      <FiRefreshCw />
                    </button>
                    <button className={styles.messageAction} title="Like">
                      <FiThumbsUp />
                    </button>
                    <button className={styles.messageAction} title="Dislike">
                      <FiThumbsDown />
                    </button>
                  </div>
                )}
              </div>
              {message.sender === "user" && (
                <div className={styles.avatar}>
                  {session.user.image ? (
                    <img src={session.user.image} alt={session.user.name} />
                  ) : (
                    <FiUser className={styles.userIcon} />
                  )}
                </div>
              )}
            </div>
          ))}

          {loading && (
            <div className={`${styles.message} ${styles.botMessage}`}>
              <div className={styles.avatar}>
                <BsRobot className={styles.botIcon} />
              </div>
              <div className={styles.messageContent}>
                <div className={styles.typingIndicator}>
                  <span></span>
                  <span></span>
                  <span></span>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Bottom Input Area - Only shown when there are messages */}
        {messages.length > 0 && (
          <form onSubmit={handleSendMessage} className={styles.inputArea}>
            <div className={styles.inputContainer}>
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="Message AI assistant..."
                className={styles.messageInput}
                disabled={loading}
              />
              <button
                type="submit"
                className={styles.sendButton}
                disabled={!input.trim() || loading}
              >
                <svg
                  width="20"
                  height="20"
                  viewBox="0 0 24 24"
                  fill="none"
                  xmlns="http://www.w3.org/2000/svg"
                >
                  <path
                    d="M22 2L11 13M22 2L15 22L11 13M11 13L2 9"
                    stroke="currentColor"
                    strokeWidth="2"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  />
                </svg>
              </button>
            </div>
            <div className={styles.inputFooter}>
              <span className={styles.disclaimer}>
                AI assistant may produce inaccurate information
              </span>
            </div>
          </form>
        )}
      </div>

      {/* Logout Dialog */}
      {showLogoutDialog && (
        <div className={styles.dialogOverlay}>
          <div className={styles.dialog}>
            <h3>Confirm Logout</h3>
            <p>Are you sure you want to log out?</p>
            <div className={styles.dialogActions}>
              <button
                className={styles.cancelButton}
                onClick={() => setShowLogoutDialog(false)}
              >
                Cancel
              </button>
              <button
                className={styles.confirmButton}
                onClick={() => signOut()}
              >
                Log Out
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Clear Conversations Dialog */}
      {showClearDialog && (
        <div className={styles.dialogOverlay}>
          <div className={styles.dialog}>
            <h3>Clear All Conversations</h3>
            <p>
              Are you sure you want to clear all conversations? This action
              cannot be undone.
            </p>
            <div className={styles.dialogActions}>
              <button
                className={styles.cancelButton}
                onClick={() => setShowClearDialog(false)}
              >
                Cancel
              </button>
              <button
                className={styles.confirmButton}
                onClick={handleClearConversations}
              >
                Clear
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}