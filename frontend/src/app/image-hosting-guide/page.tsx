'use client';

import { useState } from 'react';
import Link from 'next/link';
import ImageUploader from '@/components/ImageUploader';
import { Button } from '@/components/ui/button';
import { 
  Card, 
  CardContent, 
  CardDescription, 
  CardFooter, 
  CardHeader, 
  CardTitle 
} from '@/components/ui/card';

export default function ImageHostingGuidePage() {
  const [guideSection, setGuideSection] = useState<'intro' | 'demo' | 'options'>('intro');
  const [demoError, setDemoError] = useState<string | null>(null);
  const [uploadedUrl, setUploadedUrl] = useState<string | null>(null);

  const handleImageUploaded = (imageUrl: string) => {
    setUploadedUrl(imageUrl);
    setDemoError(null);
  };

  const handleUploadError = (error: Error) => {
    setDemoError(error.message);
  };

  return (
    <div className="max-w-4xl mx-auto py-8 px-4">
      <h1 className="text-3xl font-bold mb-8">Image Hosting Guide</h1>
      
      <div className="mb-8">
        <div className="flex border-b">
          <Button 
            variant={guideSection === 'intro' ? 'default' : 'ghost'}
            className={`rounded-none px-4 ${guideSection === 'intro' ? 'border-b-2 border-primary' : ''}`}
            onClick={() => setGuideSection('intro')}
          >
            Introduction
          </Button>
          <Button 
            variant={guideSection === 'demo' ? 'default' : 'ghost'}
            className={`rounded-none px-4 ${guideSection === 'demo' ? 'border-b-2 border-primary' : ''}`}
            onClick={() => setGuideSection('demo')}
          >
            Demo
          </Button>
          <Button 
            variant={guideSection === 'options' ? 'default' : 'ghost'}
            className={`rounded-none px-4 ${guideSection === 'options' ? 'border-b-2 border-primary' : ''}`}
            onClick={() => setGuideSection('options')}
          >
            Hosting Options
          </Button>
        </div>
      </div>
      
      {guideSection === 'intro' && (
        <div className="prose max-w-none">
          <h2>How Image Hosting Works in This Application</h2>
          <p>
            Our rentify.ai platform supports image uploads for property listings. The system is designed to:
          </p>
          <ul>
            <li>Allow property owners to upload multiple images for each property</li>
            <li>Securely store images on the server</li>
            <li>Optimize images for fast loading</li>
            <li>Set a primary image that appears in search results</li>
          </ul>
          
          <h3>How to Use Image Uploads</h3>
          <p>
            To upload images to your property listings:
          </p>
          <ol>
            <li>Navigate to your property's edit page</li>
            <li>Find the image upload section</li>
            <li>Click to browse your files or drag and drop images</li>
            <li>Select images (JPG, PNG, or GIF format, max 5MB per image)</li>
            <li>Click "Upload" to save your images</li>
          </ol>
          
          <p>
            You can select one image as the "primary" image, which will be displayed in search results and as the main image on your property page.
          </p>
        </div>
      )}
      
      {guideSection === 'demo' && (
        <div>
          <h2 className="text-2xl font-semibold mb-4">Image Upload Demo</h2>
          <p className="mb-6 text-gray-600">
            This demo shows how the image uploader works. You need to be logged in and own a property to upload real images.
          </p>
          
          <Card className="mb-6">
            <CardContent className="pt-6">
              {!uploadedUrl ? (
                <>
                  <h3 className="text-lg font-medium mb-4">Upload an image</h3>
                  <p className="text-sm text-gray-500 mb-4">
                    This demo requires you to be logged in and have a property ID.
                    For demonstration purposes, we're using property ID 1.
                  </p>
                  
                  <ImageUploader 
                    propertyId={1}
                    onImageUploaded={handleImageUploaded}
                    onError={handleUploadError}
                  />
                  
                  {demoError && (
                    <div className="mt-4 p-3 bg-red-100 border border-red-400 text-red-700 rounded text-sm">
                      {demoError}
                    </div>
                  )}
                </>
              ) : (
                <div className="text-center">
                  <h3 className="text-lg font-medium mb-4">Image Uploaded Successfully!</h3>
                  <p className="mb-4">Your image was uploaded to:</p>
                  <div className="mb-4 p-2 bg-gray-100 text-gray-800 rounded-md text-sm overflow-auto">
                    <code>{uploadedUrl}</code>
                  </div>
                  <Button
                    onClick={() => setUploadedUrl(null)}
                  >
                    Upload Another Image
                  </Button>
                </div>
              )}
            </CardContent>
          </Card>
          
          <div className="bg-yellow-50 border-l-4 border-yellow-400 p-4">
            <div className="flex">
              <div className="flex-shrink-0">
                <svg className="h-5 w-5 text-yellow-400" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                </svg>
              </div>
              <div className="ml-3">
                <p className="text-sm text-yellow-700">
                  Note: This demo will show authorization errors if you're not logged in or don't have permission for the property.
                </p>
              </div>
            </div>
          </div>
        </div>
      )}
      
      {guideSection === 'options' && (
        <div className="prose max-w-none">
          <h2>Image Hosting Options</h2>
          
          <p>
            There are several options for hosting images in a production environment:
          </p>
          
          <Card className="mb-6">
            <CardHeader>
              <CardTitle>1. Default: Server Storage (Current Implementation)</CardTitle>
            </CardHeader>
            <CardContent>
              <p>
                In the current implementation, images are uploaded to the Django server and stored in a
                media directory. This works well for development and small-scale deployments.
              </p>
              <ul>
                <li><strong>Pros:</strong> Simple setup, no additional services required</li>
                <li><strong>Cons:</strong> Limited scalability, server disk space constraints</li>
              </ul>
            </CardContent>
          </Card>
          
          <Card className="mb-6">
            <CardHeader>
              <CardTitle>2. AWS S3 (Recommended for Production)</CardTitle>
            </CardHeader>
            <CardContent>
              <p>
                For production environments, we recommend using Amazon S3 for image storage.
                This is already configured in the project settings but needs to be enabled.
              </p>
              <ul>
                <li><strong>Pros:</strong> Highly scalable, reliable, cost-effective for storage</li>
                <li><strong>Cons:</strong> Requires AWS account and configuration</li>
              </ul>
            </CardContent>
          </Card>
          
          <Card className="mb-6">
            <CardHeader>
              <CardTitle>3. Cloudinary</CardTitle>
            </CardHeader>
            <CardContent>
              <p>
                Cloudinary is a cloud-based image and video management service that offers
                optimization, transformation, and delivery capabilities.
              </p>
              <ul>
                <li><strong>Pros:</strong> Image optimization, transformations, CDN delivery</li>
                <li><strong>Cons:</strong> Additional service to manage, potential costs</li>
              </ul>
            </CardContent>
          </Card>
          
          <Card className="mb-6">
            <CardHeader>
              <CardTitle>4. Firebase Storage</CardTitle>
            </CardHeader>
            <CardContent>
              <p>
                Firebase Storage provides secure file uploads and downloads for Firebase apps.
              </p>
              <ul>
                <li><strong>Pros:</strong> Easy integration with Firebase ecosystem, good free tier</li>
                <li><strong>Cons:</strong> Less flexible than S3 for some use cases</li>
              </ul>
            </CardContent>
          </Card>
          
          <h3>Setting Up AWS S3 (Recommended)</h3>
          <p>
            To configure S3 storage:
          </p>
          <ol>
            <li>Create an AWS account and S3 bucket</li>
            <li>Configure IAM permissions</li>
            <li>Update your Django settings with AWS credentials</li>
            <li>Enable the S3 storage backend in settings</li>
          </ol>
          
          <div className="bg-gray-100 p-4 rounded-md">
            <pre><code>
{`# In backend/rental_platform/settings.py

# Enable S3 storage
USE_S3 = os.environ.get('USE_S3') == 'TRUE'

if USE_S3:
    # AWS settings
    AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID')
    AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')
    AWS_STORAGE_BUCKET_NAME = os.environ.get('AWS_STORAGE_BUCKET_NAME')
    AWS_DEFAULT_ACL = None
    AWS_S3_CUSTOM_DOMAIN = f'{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com'
    AWS_S3_OBJECT_PARAMETERS = {'CacheControl': 'max-age=86400'}
    
    # S3 static settings
    STATIC_LOCATION = 'static'
    STATIC_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/{STATIC_LOCATION}/'
    STATICFILES_STORAGE = 'rental_platform.storage_backends.StaticStorage'
    
    # S3 media settings
    MEDIA_LOCATION = 'media'
    MEDIA_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/{MEDIA_LOCATION}/'
    DEFAULT_FILE_STORAGE = 'rental_platform.storage_backends.MediaStorage'
else:
    STATIC_URL = '/static/'
    STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
    MEDIA_URL = '/media/'
    MEDIA_ROOT = os.path.join(BASE_DIR, 'media')`}
            </code></pre>
          </div>
          
          <p className="mt-4">
            <Button asChild variant="link" className="p-0 h-auto">
              <Link href="https://docs.aws.amazon.com/AmazonS3/latest/userguide/Welcome.html" target="_blank" rel="noopener noreferrer">
                Learn more about AWS S3 →
              </Link>
            </Button>
          </p>
        </div>
      )}
    </div>
  );
} 