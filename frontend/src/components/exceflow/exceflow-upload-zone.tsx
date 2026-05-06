'use client';

import * as React from 'react';
import Image from 'next/image';
import { CloudUpload, Upload } from 'lucide-react';

import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';

const EXCEFLOW_UPLOAD_ILLUSTRATION =
  'https://lh3.googleusercontent.com/aida/ADBb0uhk3gzCwIug9rKmH9CJUsJkzlz8YBDQzcxOQHYegK6SjYDJijHvL9jfzaLoBv7phMg2igz5wfprmiIQLil4IjCqRrqyqa3LWSjtpzHFJv0YUk8fLORmvVzvvG3VGXOzMRFvfrdetCTJiJFSNekNTBfD-ee77WjkGZgoTQ2IycKvTB4HuVoKUQe_zEghcgeOoprhw5T-rrEWJUW1kfsFJYOAUw1TdWbJ4SiB-VqMAAuEQymSZcPKsU_6idhvuLFF5QWGcQR_2KOLjak';

type ExceflowUploadZoneProps = {
  file: File | null;
  onFileChange: (file: File | null) => void;
  disabled?: boolean;
  maxLabel?: string;
};

export function ExceflowUploadZone({
  file,
  onFileChange,
  disabled,
  maxLabel = 'or choose a file from your computer',
}: ExceflowUploadZoneProps) {
  const inputRef = React.useRef<HTMLInputElement>(null);
  const [dragActive, setDragActive] = React.useState(false);

  function pickFiles(files: FileList | null) {
    const f = files?.[0];
    if (f && f.type === 'application/pdf') {
      onFileChange(f);
    }
  }

  return (
    <div
      className={cn(
        'bg-card group text-foreground flex min-h-[400px] cursor-pointer flex-col items-center justify-center rounded-xl border border-border p-8 text-center transition-colors duration-300',
        dragActive
          ? 'border-exceflow-cta shadow-md shadow-exceflow-cta/10'
          : 'hover:border-exceflow-cta',
        disabled && 'pointer-events-none opacity-50',
      )}
      onClick={() => !disabled && inputRef.current?.click()}
      onDragEnter={(e) => {
        e.preventDefault();
        setDragActive(true);
      }}
      onDragLeave={(e) => {
        e.preventDefault();
        setDragActive(false);
      }}
      onDragOver={(e) => e.preventDefault()}
      onDrop={(e) => {
        e.preventDefault();
        setDragActive(false);
        pickFiles(e.dataTransfer.files);
      }}>
      <input
        ref={inputRef}
        type='file'
        accept='application/pdf,.pdf'
        className='hidden'
        disabled={disabled}
        onChange={(e) => pickFiles(e.target.files)}
      />
      <div className='mb-6 opacity-90'>
        <Image
          src={EXCEFLOW_UPLOAD_ILLUSTRATION}
          alt=''
          width={192}
          height={160}
          className='pointer-events-none mx-auto h-auto w-48 select-none'
          priority={false}
        />
      </div>
      <div className='flex flex-col items-center'>
        <CloudUpload
          className='text-muted-foreground mb-4 size-12'
          strokeWidth={1.25}
          aria-hidden
        />
        <h2 className='text-foreground mb-1 text-xl font-semibold tracking-tight'>
          Drag and drop PDF here
        </h2>
        <p className='text-muted-foreground mb-8 text-sm'>{maxLabel}</p>
        <Button
          type='button'
          variant='outline'
          className='text-foreground border-border bg-card hover:bg-muted rounded-lg px-10 font-medium'
          onClick={(e) => {
            e.stopPropagation();
            inputRef.current?.click();
          }}
          disabled={disabled}>
          <Upload className='size-4' aria-hidden />
          Choose File
        </Button>
        {file && (
          <p className='text-muted-foreground mt-6 max-w-full truncate px-2 text-sm'>
            <span className='text-foreground font-medium'>{file.name}</span>
            <span>
              {' '}
              · {(file.size / 1024).toFixed(0)} KB
            </span>
          </p>
        )}
      </div>
    </div>
  );
}
