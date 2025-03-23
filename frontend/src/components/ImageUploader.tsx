'use client';

import { useState, useRef } from 'react';
import Image from 'next/image';
import { propertyService } from '@/app/api/services/propertyService';

interface ImageUploaderProps {
  propertyId: number | string;
  onImageUploaded?: (imageUrl: string) => void;
  onError?: (error: Error) => void;
  className?: string;
}

export default function ImageUploader({ 
  propertyId, 
  onImageUploaded, 
  onError,
  className = '' 
}: ImageUploaderProps) {
  const [isUploading, setIsUploading] = useState(false);
  const [preview, setPreview] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    // Check file type
    if (!file.type.match('image.*')) {
      alert('Please select an image file');
      return;
    }

    // Check file size (max 5MB)
    if (file.size > 5 * 1024 * 1024) {
      alert('File size should be less than 5MB');
      return;
    }

    // Create preview
    const reader = new FileReader();
    reader.onload = (e) => {
      setPreview(e.target?.result as string);
    };
    reader.readAsDataURL(file);
  };

  const handleUpload = async () => {
    if (!fileInputRef.current?.files?.[0]) {
      alert('Please select an image first');
      return;
    }

    setIsUploading(true);
    
    try {
      const file = fileInputRef.current.files[0];
      const formData = new FormData();
      formData.append('image', file);
      
      // Optional metadata
      formData.append('is_primary', 'true');  // Make this the primary image
      
      const response = await propertyService.uploadPropertyImage(propertyId, formData);
      
      // Call the callback with the uploaded image URL
      if (onImageUploaded && response.image_url) {
        onImageUploaded(response.image_url);
      }
      
      // Clear the file input and preview
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
      setPreview(null);
      
    } catch (error) {
      console.error('Failed to upload image:', error);
      if (onError && error instanceof Error) {
        onError(error);
      }
    } finally {
      setIsUploading(false);
    }
  };

  const triggerFileInput = () => {
    fileInputRef.current?.click();
  };

  return (
    <div className={`flex flex-col items-center ${className}`}>
      <div 
        className="border-2 border-dashed border-gray-300 rounded-lg p-6 w-full text-center cursor-pointer hover:bg-gray-50 transition-colors mb-4"
        onClick={triggerFileInput}
      >
        {preview ? (
          <div className="relative h-48 w-full">
            <Image 
              src={preview} 
              alt="Image preview" 
              fill
              className="object-contain rounded-md"
            />
          </div>
        ) : (
          <>
            <svg xmlns="http://www.w3.org/2000/svg" className="h-12 w-12 mx-auto mb-2 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
            </svg>
            <p className="text-gray-500">Click to upload image</p>
            <p className="text-sm text-gray-400 mt-1">JPG, PNG, GIF (max 5MB)</p>
          </>
        )}
      </div>
      
      <input
        type="file"
        accept="image/*"
        className="hidden"
        ref={fileInputRef}
        onChange={handleFileSelect}
      />
      
      {preview && (
        <button
          onClick={handleUpload}
          disabled={isUploading}
          className="bg-blue-600 text-white px-4 py-2 rounded-md disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isUploading ? 'Uploading...' : 'Upload Image'}
        </button>
      )}
    </div>
  );
} 