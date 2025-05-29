import { useState, useEffect } from 'react';
import { useSession, signOut } from 'next-auth/react';
import { useRouter } from 'next/router';
import styles from '../styles/Admin.module.css';
import axios from 'axios';

export default function AdminDashboard() {
  const { data: session, status } = useSession();
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [docId, setDocId] = useState('');
  const [docContent, setDocContent] = useState('');
  const [documents, setDocuments] = useState([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [isUploading, setIsUploading] = useState(false);
  const [activeTab, setActiveTab] = useState('upload');
  const [showLogoutConfirm, setShowLogoutConfirm] = useState(false);

  const BACKEND_API_URL = "http://127.0.0.1:5010"; // Backend API URL

  useEffect(() => {
    if (status === 'unauthenticated') {
      router.push('/auth/login');
    } else if (status === 'authenticated') {
      // Check if user is admin
      const userRole = localStorage.getItem('userRole');
      if (userRole !== 'admin') {
        router.push('/');
      }
    }
  }, [status, router]);
const handleUserClick = () => {
    router.push("/");
  };
  useEffect(() => {
    if (status === 'authenticated' && activeTab === 'view') {
      fetchDocuments();
    }
  }, [status, activeTab]);

  const fetchDocuments = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`${BACKEND_API_URL}/list_documents`);
      if (response.status === 200) {
        setDocuments(response.data.documents || []);
      }
      setLoading(false);
    } catch (error) {
      console.error('Error fetching documents:', error);
      setLoading(false);
    }
  };

  const handleStoreDocument = async () => {
    if (docId && docContent) {
      try {
        setIsUploading(true);
        const response = await axios.post(`${BACKEND_API_URL}/store_data/`, {
          text: docContent,
          data_id: docId
        });

        if (response.status === 200) {
          alert('Document stored successfully');
          setDocId('');
          setDocContent('');
          if (activeTab === 'view') {
            await fetchDocuments();
          }
        } else {
          alert('Error storing document');
        }
        setIsUploading(false);
      } catch (error) {
        console.error('Error storing document:', error);
        setIsUploading(false);
        alert('Failed to store document. Please try again.');
      }
    } else {
      alert('Please provide both Document ID and Content');
    }
  };

  const handleDeleteDocument = async (docId) => {
    if (confirm('Are you sure you want to delete this document?')) {
      try {
        setLoading(true);
        const response = await axios.delete(`${BACKEND_API_URL}/delete_data/${docId}`);
        if (response.status === 200) {
          alert('Document deleted successfully');
          await fetchDocuments();
        }
        setLoading(false);
      } catch (error) {
        console.error('Error deleting document:', error);
        setLoading(false);
        alert('Failed to delete document. Please try again.');
      }
    }
  };

  const handleLogout = () => {
    setShowLogoutConfirm(true);
  };

  const confirmLogout = () => {
    signOut({ callbackUrl: '/auth/login' });
  };

  const filteredDocuments = documents.filter(doc => 
    doc.toLowerCase().includes(searchQuery.toLowerCase())
  );

  if (status !== 'authenticated') {
    return (
      <div className={styles.loadingScreen}>
        <div className={styles.loadingSpinner}></div>
        <p>Authenticating...</p>
      </div>
    );
  }

  return (
    <div className={styles.container}>
      {/* Logout Confirmation Dialog */}
      {showLogoutConfirm && (
        <div className={styles.confirmDialogOverlay}>
          <div className={styles.confirmDialog}>
            <h3>Confirm Logout</h3>
            <p>Are you sure you want to log out?</p>
            <div className={styles.dialogButtons}>
              <button 
                className={styles.cancelButton}
                onClick={() => setShowLogoutConfirm(false)}
              >
                Cancel
              </button>
              <button 
                className={styles.confirmButton}
                onClick={confirmLogout}
              >
                Logout
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Sidebar */}
      <div className={styles.sidebar}>
        <div className={styles.sidebarHeader}>
          <div className={styles.userInfo}>
            <div className={styles.userAvatar}>
              {session.user.image ? (
                <img src={session.user.image} alt={session.user.name} />
              ) : (
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M16 7C16 9.20914 14.2091 11 12 11C9.79086 11 8 9.20914 8 7C8 4.79086 9.79086 3 12 3C14.2091 3 16 4.79086 16 7Z" stroke="currentColor" strokeWidth="2" />
                  <path d="M12 14C8.13401 14 5 17.134 5 21H19C19 17.134 15.866 14 12 14Z" stroke="currentColor" strokeWidth="2" />
                </svg>
              )}
            </div>
            <div className={styles.userDetails}>
              <span className={styles.userName}>{session.user.name}</span>
              <span className={styles.userEmail}>{session.user.email}</span>
            </div>
          </div>
          <button className={styles.signOutButton} onClick={handleLogout}>
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M17 17H17.01M17 13H17.01M12 13H12.01M7 13H7.01M7 17H7.01M12 17H12.01M16 17H16.01M21 12C21 16.9706 16.9706 21 12 21C7.02944 21 3 16.9706 3 12C3 7.02944 7.02944 3 12 3C16.9706 3 21 7.02944 21 12ZM13 7H11V12H13V7Z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
          </button>
        </div>

        <div className={styles.sidebarMenu}>
          <button 
            className={`${styles.menuButton} ${activeTab === 'upload' ? styles.active : ''}`}
            onClick={() => setActiveTab('upload')}
          >
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M12 15V3M12 3L8 7M12 3L16 7M8 21H16C17.1046 21 18 20.1046 18 19V15C18 13.8954 17.1046 13 16 13H8C6.89543 13 6 13.8954 6 15V19C6 20.1046 6.89543 21 8 21Z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
            Upload Document
          </button>
          <button 
            className={`${styles.menuButton} ${activeTab === 'upload' ? styles.active : ''}`}
            onClick={handleUserClick}
          >
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M16 7C16 9.20914 14.2091 11 12 11C9.79086 11 8 9.20914 8 7C8 4.79086 9.79086 3 12 3C14.2091 3 16 4.79086 16 7Z" stroke="currentColor" strokeWidth="2" />
                  <path d="M12 14C8.13401 14 5 17.134 5 21H19C19 17.134 15.866 14 12 14Z" stroke="currentColor" strokeWidth="2" />
                </svg>
            User Panel
          </button>
        </div>
      </div>

      {/* Main Content */}
      <div className={styles.mainContent}>
        <div className={styles.contentHeader}>
          <h2>Document Management System</h2>
          <p>Upload and manage your knowledge base documents</p>
        </div>

        {activeTab === 'upload' ? (
          <div className={styles.uploadSection}>
            <div className={styles.uploadCard}>
              <h3>Upload New Document</h3>
              <p className={styles.cardDescription}>Add documents to your knowledge base to enhance the chatbot responses</p>
              
              <div className={styles.formGroup}>
                <label>Document ID</label>
                <input
                  type="text"
                  placeholder="Enter a unique document ID"
                  value={docId}
                  onChange={(e) => setDocId(e.target.value)}
                  className={styles.inputField}
                />
              </div>
              
              <div className={styles.formGroup}>
                <label>Document Content</label>
                <textarea
                  placeholder="Paste your document content here..."
                  value={docContent}
                  onChange={(e) => setDocContent(e.target.value)}
                  className={styles.textareaField}
                  rows={8}
                />
              </div>
              
              <button
                className={styles.uploadButton}
                onClick={handleStoreDocument}
                disabled={isUploading || !docId || !docContent}
              >
                {isUploading ? (
                  <>
                    <span className={styles.spinner}></span>
                    Uploading...
                  </>
                ) : (
                  <>
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                      <path d="M12 15V3M12 3L8 7M12 3L16 7M8 21H16C17.1046 21 18 20.1046 18 19V15C18 13.8954 17.1046 13 16 13H8C6.89543 13 6 13.8954 6 15V19C6 20.1046 6.89543 21 8 21Z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                    </svg>
                    Upload Document
                  </>
                )}
              </button>
            </div>
          </div>
        ) : (
          <div className={styles.viewSection}>
            <div className={styles.searchBar}>
              <input
                type="text"
                placeholder="Search documents..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className={styles.searchInput}
              />
              <button 
                className={styles.refreshButton}
                onClick={fetchDocuments}
                disabled={loading}
              >
                {loading ? (
                  <span className={styles.smallSpinner}></span>
                ) : (
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M21 12C21 16.9706 16.9706 21 12 21C7.02944 21 3 16.9706 3 12C3 7.02944 7.02944 3 12 3C15.1886 3 18.0227 4.43149 19.9016 6.66667M19.9016 6.66667V3M19.9016 6.66667H16.5683" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                  </svg>
                )}
              </button>
            </div>
            
            {loading ? (
              <div className={styles.loadingContainer}>
                <div className={styles.loadingSpinner}></div>
                <p>Loading documents...</p>
              </div>
            ) : (
              <div className={styles.documentsGrid}>
                {filteredDocuments.length > 0 ? (
                  filteredDocuments.map((doc, index) => (
                    <div key={index} className={styles.documentCard}>
                      <div className={styles.documentHeader}>
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                          <path d="M9 12H15M9 8H15M9 16H12M21 12C21 16.9706 16.9706 21 12 21C7.02944 21 3 16.9706 3 12C3 7.02944 7.02944 3 12 3C16.9706 3 21 7.02944 21 12Z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                        </svg>
                        <span className={styles.documentId}>{doc}</span>
                      </div>
                      <div className={styles.documentActions}>
                        <button 
                          className={styles.viewButton}
                          onClick={() => {
                            // Implement view functionality if needed
                            alert(`Viewing document: ${doc}`);
                          }}
                        >
                          View
                        </button>
                        <button 
                          className={styles.deleteButton}
                          onClick={() => handleDeleteDocument(doc)}
                        >
                          Delete
                        </button>
                      </div>
                    </div>
                  ))
                ) : (
                  <div className={styles.emptyState}>
                    <svg width="48" height="48" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                      <path d="M9 12H15M9 8H15M9 16H12M21 12C21 16.9706 16.9706 21 12 21C7.02944 21 3 16.9706 3 12C3 7.02944 7.02944 3 12 3C16.9706 3 21 7.02944 21 12Z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                    </svg>
                    <h4>No documents found</h4>
                    <p>Upload your first document to get started</p>
                    <button 
                      className={styles.uploadButton}
                      onClick={() => setActiveTab('upload')}
                    >
                      Upload Document
                    </button>
                  </div>
                )}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}