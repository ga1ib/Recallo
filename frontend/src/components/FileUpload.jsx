import React from "react";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { faPlus } from "@fortawesome/free-solid-svg-icons";

const FileUpload = ({ onFileSelect }) => {
  const handleFileChange = (event) => {
    const file = event.target.files[0];
    if (file && onFileSelect) {
      onFileSelect(file);
    }
  };

  return (
    <>
      <label
        htmlFor="file-upload"
        className="upload-icon chat_ic"
        title="Upload file"
      >
        <FontAwesomeIcon icon={faPlus} style={{ color: "#ffffff" }} />
      </label>
      <input
        type="file"
        id="file-upload"
        style={{ display: "none" }}
        accept=".pdf,.doc,.docx,.png,.jpg,.jpeg,.webp"
        onChange={handleFileChange}
      />
    </>
  );
};

export default FileUpload;
