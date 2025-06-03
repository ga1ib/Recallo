import React, { useRef, useContext } from 'react';
import { ChatContext } from '../context/ChatContext';
import { FaFilePdf, FaImage } from 'react-icons/fa';
import Tesseract from 'tesseract.js';

export default function FileUpload() {
  const fileInputRef = useRef();
  const { addMessage } = useContext(ChatContext);

  const handleFileChange = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    if (file.type === 'application/pdf') {
      addMessage({ sender: 'user', text: `📄 Uploaded PDF: ${file.name}` });
      // TODO: send to backend for parsing/summarization
    } else if (file.type.startsWith('image/')) {
      addMessage({ sender: 'user', text: `🖼️ Uploaded Image: ${file.name}` });
      const {
        data: { text },
      } = await Tesseract.recognize(file, 'eng');
      addMessage({
        sender: 'bot',
        text: `OCR Result: ${text.slice(0, 200)}...`,
      });
      // TODO: send OCR text to backend for summarization
    } else {
      addMessage({ sender: 'bot', text: 'Unsupported file type.' });
    }
    e.target.value = null;
  };

  return (
    <div className="flex space-x-4">
      <button
        onClick={() => fileInputRef.current.click()}
        className="flex items-center space-x-2 bg-green-500 hover:bg-green-600 text-white px-4 py-2 rounded-lg transition-colors"
      >
        <FaFilePdf />
        <span>Upload PDF</span>
      </button>
      <button
        onClick={() => fileInputRef.current.click()}
        className="flex items-center space-x-2 bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded-lg transition-colors"
      >
        <FaImage />
        <span>Upload Image</span>
      </button>
      <input
        type="file"
        accept="application/pdf, image/*"
        className="hidden"
        ref={fileInputRef}
        onChange={handleFileChange}
      />
    </div>
  );
}
