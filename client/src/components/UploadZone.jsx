import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { Upload, Loader } from 'lucide-react';
import axios from 'axios';

const UploadZone = ({ onAnalysisComplete }) => {
    const [isDragging, setIsDragging] = useState(false);
    const [isUploading, setIsUploading] = useState(false);

    const handleDragOver = (e) => {
        e.preventDefault();
        setIsDragging(true);
    };

    const handleDragLeave = () => {
        setIsDragging(false);
    };

    const handleDrop = async (e) => {
        e.preventDefault();
        setIsDragging(false);
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            await uploadFiles(files);
        }
    };

    const uploadFiles = async (fileList) => {
        setIsUploading(true);
        const formData = new FormData();

        for (let i = 0; i < fileList.length; i++) {
            formData.append('files', fileList[i]);
        }

        try {
            // Assuming backend runs on 5001
            const response = await axios.post('http://localhost:5001/upload', formData, {
                headers: {
                    'Content-Type': 'multipart/form-data'
                }
            });
            onAnalysisComplete(response.data);
        } catch (error) {
            console.error("Upload failed", error);
            alert("Upload failed. Ensure backend is running on port 5001.");
        } finally {
            setIsUploading(false);
        }
    };


    const fileInputRef = React.useRef(null);

    const onButtonClick = () => {
        fileInputRef.current.click();
    };

    const onFileInputChange = (e) => {
        if (e.target.files && e.target.files.length > 0) {
            uploadFiles(e.target.files);
        }
    };

    return (
        <div className="flex flex-col items-center justify-center p-8">
            <input
                type="file"
                ref={fileInputRef}
                className="hidden"
                multiple
                onChange={onFileInputChange}
            />
            <motion.div
                layout
                initial={{ scale: 0.9, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                onClick={onButtonClick}
                className={`w-full max-w-3xl h-64 border-2 border-dashed rounded-2xl flex flex-col items-center justify-center cursor-pointer transition-all duration-300 ${isDragging ? 'border-accent bg-accent/10 scale-105 shadow-[0_0_30px_rgba(139,92,246,0.3)]' : 'border-white/20 hover:border-accent/50 hover:bg-white/5'
                    }`}
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
                onDrop={handleDrop}
            >
                {isUploading ? (
                    <div className="flex flex-col items-center gap-4">
                        <Loader className="w-10 h-10 text-accent animate-spin" />
                        <p className="text-gray-300 font-light">Analyzing content & Generating Graph...</p>
                    </div>
                ) : (
                    <div className="flex flex-col items-center gap-4 text-gray-400 group">
                        <div className="p-4 rounded-full bg-white/5 group-hover:bg-accent/20 transition-colors">
                            <Upload className="w-8 h-8 text-accent" />
                        </div>
                        <div className="text-center">
                            <p className="text-lg font-medium text-white mb-2">Drag & Drop files here</p>
                            <p className="text-sm">Multimodal Input (Multiple files allowed: PDF, PPT, Audio, Video)</p>
                            <button className="mt-4 px-4 py-2 bg-accent hover:bg-accent/80 text-white rounded-lg text-sm font-medium transition-colors">
                                Select File
                            </button>
                        </div>
                    </div>
                )}
            </motion.div>

        </div>
    );
};
export default UploadZone;
