import React from 'react';

const History = ({ isLoggedIn }) => {
  return (
    <div className="history">
      {isLoggedIn ? (
        <>
          <h3>Chat History</h3>
          {/* Your normal history content here */}
        </>
      ) : (
        <div className="history-logged-out-message">
          <h3>Chat History</h3>
          <p>Please <strong>sign in</strong> to access your chat history.</p>
        </div>
      )}
    </div>
  );
};

export default History;
