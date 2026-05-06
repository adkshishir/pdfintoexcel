'use client';

import * as React from 'react';

import { Label } from '@/components/ui/label';
import { RadioGroupItem } from '@/components/ui/radio-group';
import { cn } from '@/lib/utils';

export function ExceflowRadioTile({
  value,
  currentValue,
  id,
  disabled,
  className,
  leadingIcon,
  children,
}: {
  value: string;
  currentValue: string;
  id: string;
  disabled?: boolean;
  className?: string;
  leadingIcon?: React.ReactNode;
  children: React.ReactNode;
}) {
  const selected = currentValue === value;
  return (
    <div className='relative'>
      <RadioGroupItem
        value={value}
        id={id}
        disabled={disabled}
        className='peer sr-only'
      />
      <Label
        htmlFor={id}
        className={cn(
          'group text-foreground flex cursor-pointer flex-col gap-1 rounded-xl border-2 p-4 text-left transition-[border-color,background-color,box-shadow] duration-200',
          selected
            ? 'border-exceflow-cta bg-exceflow-cta/[0.04] shadow-sm'
            : 'border-border bg-card hover:border-exceflow-cta/60',
          disabled && 'pointer-events-none opacity-50',
          className,
        )}>
        {leadingIcon}
        {children}
      </Label>
    </div>
  );
}
