'use client';

import * as React from 'react';
import { CloudUpload, Upload } from 'lucide-react';

import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';

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
  maxLabel = 'PDF up to your plan limit · one file at a time',
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
        'group bg-muted/30 flex min-h-[240px] cursor-pointer flex-col items-center justify-center rounded-2xl border-2 border-dashed border-border px-6 py-12 text-center transition-colors duration-200',
        dragActive
          ? 'border-primary/50 bg-primary/[0.03]'
          : 'hover:border-primary/35 hover:bg-muted/50',
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
      <CloudUpload
        className='text-muted-foreground mb-4 size-11'
        strokeWidth={1.25}
        aria-hidden
      />
      <h2 className='text-foreground text-base font-semibold tracking-tight'>
        Drag and drop your PDF
      </h2>
      <p className='text-muted-foreground mt-1 max-w-sm text-sm'>{maxLabel}</p>
      <Button
        type='button'
        variant='outline'
        className='mt-6 rounded-xl border-border shadow-sm'
        onClick={(e) => {
          e.stopPropagation();
          inputRef.current?.click();
        }}
        disabled={disabled}>
        <Upload className='size-4' aria-hidden />
        Choose file
      </Button>
      {file && (
        <p className='text-muted-foreground mt-6 max-w-full truncate text-sm'>
          <span className='text-foreground font-medium'>{file.name}</span>
          <span> · {(file.size / 1024).toFixed(0)} KB</span>
        </p>
      )}
    </div>
  );
}
