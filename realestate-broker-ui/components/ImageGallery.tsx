'use client'
import React, { useState } from 'react'
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { ChevronLeft, ChevronRight, X, ZoomIn } from 'lucide-react'
import Image from 'next/image'

interface ImageGalleryProps {
  images: string[]
  className?: string
  maxDisplay?: number
  showThumbnails?: boolean
  size?: 'sm' | 'md' | 'lg'
}

export default function ImageGallery({ 
  images, 
  className = '', 
  maxDisplay = 3,
  showThumbnails = true,
  size = 'md'
}: ImageGalleryProps) {
  const [selectedImage, setSelectedImage] = useState<number | null>(null)
  const [isFullscreen, setIsFullscreen] = useState(false)

  if (!images || images.length === 0) {
    return (
      <div className={`flex items-center justify-center bg-gray-100 rounded-lg ${className}`}>
        <div className="text-center text-gray-500 p-4">
          <div className="text-sm">אין תמונות זמינות</div>
        </div>
      </div>
    )
  }

  const sizeClasses = {
    sm: 'h-16 w-16 sm:h-20 sm:w-20',
    md: 'h-24 w-24 sm:h-32 sm:w-32',
    lg: 'h-32 w-32 sm:h-48 sm:w-48'
  }

  const displayImages = images.slice(0, maxDisplay)
  const remainingCount = images.length - maxDisplay

  const openFullscreen = (index: number) => {
    setSelectedImage(index)
    setIsFullscreen(true)
  }

  const closeFullscreen = () => {
    setIsFullscreen(false)
    setSelectedImage(null)
  }

  const nextImage = () => {
    if (selectedImage !== null) {
      setSelectedImage((selectedImage + 1) % images.length)
    }
  }

  const prevImage = () => {
    if (selectedImage !== null) {
      setSelectedImage(selectedImage === 0 ? images.length - 1 : selectedImage - 1)
    }
  }

  return (
    <>
      <div className={`flex gap-1 sm:gap-2 ${className}`}>
        {displayImages.map((image, index) => (
          <div key={index} className="relative group">
            <div className={`relative ${sizeClasses[size]} rounded-lg overflow-hidden cursor-pointer`}>
              <Image
                src={image}
                alt={`תמונה ${index + 1}`}
                fill
                className="object-cover transition-transform group-hover:scale-105"
                onClick={() => openFullscreen(index)}
                sizes="(max-width: 640px) 64px, (max-width: 768px) 80px, 128px"
                priority={index === 0}
              />
              <div className="absolute inset-0 bg-black bg-opacity-0 group-hover:bg-opacity-20 transition-all duration-200 flex items-center justify-center">
                <ZoomIn className="h-6 w-6 text-white opacity-0 group-hover:opacity-100 transition-opacity" />
              </div>
            </div>
            {index === maxDisplay - 1 && remainingCount > 0 && (
              <div 
                className="absolute inset-0 bg-black bg-opacity-50 flex items-center justify-center rounded-lg cursor-pointer"
                onClick={() => openFullscreen(maxDisplay - 1)}
              >
                <span className="text-white font-semibold text-lg">
                  +{remainingCount}
                </span>
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Fullscreen Modal */}
      <Dialog open={isFullscreen} onOpenChange={setIsFullscreen}>
        <DialogContent className="max-w-4xl max-h-[90vh] p-0">
          <DialogHeader className="p-4 pb-0">
            <div className="flex items-center justify-between">
              <DialogTitle>
                תמונה {selectedImage !== null ? selectedImage + 1 : 1} מתוך {images.length}
              </DialogTitle>
              <Button
                variant="ghost"
                size="icon"
                onClick={closeFullscreen}
              >
                <X className="h-4 w-4" />
              </Button>
            </div>
          </DialogHeader>
          
          <div className="relative flex-1 p-2 sm:p-4">
            {selectedImage !== null && (
              <div className="relative h-64 sm:h-96 md:h-[500px]">
                <Image
                  src={images[selectedImage]}
                  alt={`תמונה ${selectedImage + 1}`}
                  fill
                  className="object-contain"
                  sizes="(max-width: 640px) 100vw, (max-width: 768px) 90vw, 80vw"
                  priority
                />
                
                {/* Navigation buttons */}
                {images.length > 1 && (
                  <>
                    <Button
                      variant="ghost"
                      size="icon"
                      className="absolute start-2 top-1/2 -translate-y-1/2 bg-black/50 hover:bg-black/70 text-white"
                      onClick={prevImage}
                    >
                      <ChevronLeft className="h-4 w-4 rtl:rotate-180" />
                    </Button>
                    <Button
                      variant="ghost"
                      size="icon"
                      className="absolute end-2 top-1/2 -translate-y-1/2 bg-black/50 hover:bg-black/70 text-white"
                      onClick={nextImage}
                    >
                      <ChevronRight className="h-4 w-4 rtl:rotate-180" />
                    </Button>
                  </>
                )}
              </div>
            )}
          </div>

          {/* Thumbnail strip */}
          {showThumbnails && images.length > 1 && (
            <div className="p-2 sm:p-4 pt-0">
              <div className="flex gap-1 sm:gap-2 overflow-x-auto">
                {images.map((image, index) => (
                  <div
                    key={index}
                    className={`relative h-12 w-12 sm:h-16 sm:w-16 rounded-lg overflow-hidden cursor-pointer border-2 transition-all flex-shrink-0 ${
                      selectedImage === index ? 'border-primary' : 'border-transparent'
                    }`}
                    onClick={() => setSelectedImage(index)}
                  >
                    <Image
                      src={image}
                      alt={`תמונה ${index + 1}`}
                      fill
                      className="object-cover"
                      sizes="(max-width: 640px) 48px, 64px"
                    />
                  </div>
                ))}
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </>
  )
}
