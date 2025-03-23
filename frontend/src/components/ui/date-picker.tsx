"use client";

import * as React from "react";
import { format } from "date-fns";
import { Calendar as CalendarIcon } from "lucide-react";
import { DayPickerSingleProps } from "react-day-picker";

import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Calendar } from "@/components/ui/calendar";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";

interface DatePickerProps {
  date: Date | undefined;
  setDate: (date: Date | undefined) => void;
  unavailableDates?: string[];
  label?: string;
  disabled?: boolean;
  placeholder?: string;
  className?: string;
  minDate?: Date;
}

export function DatePicker({
  date,
  setDate,
  unavailableDates = [],
  label,
  disabled = false,
  placeholder = "Select date",
  className,
  minDate,
}: DatePickerProps) {
  // Convert string dates to Date objects for react-day-picker
  const disabledDays = React.useMemo(() => {
    return unavailableDates.map(dateStr => new Date(dateStr));
  }, [unavailableDates]);

  // Disable dates in the past and before minDate if provided
  const isDateDisabled = React.useCallback(
    (day: Date) => {
      // Check if the date is in the past
      const today = new Date();
      today.setHours(0, 0, 0, 0);
      if (day < today) return true;

      // Check if date is before or equal to minDate (for checkout)
      if (minDate) {
        const minDateCopy = new Date(minDate);
        minDateCopy.setHours(0, 0, 0, 0);
        if (day.getTime() <= minDateCopy.getTime()) return true;
      }

      // Check if the date is in the list of unavailable dates
      return disabledDays.some(disabledDate => {
        return (
          disabledDate.getDate() === day.getDate() &&
          disabledDate.getMonth() === day.getMonth() &&
          disabledDate.getFullYear() === day.getFullYear()
        );
      }); 
    },
    [disabledDays, minDate]
  );

  // Additional props for the Calendar component
  const calendarProps: Partial<DayPickerSingleProps> = {
    mode: "single",
    selected: date,
    onSelect: setDate,
    disabled: isDateDisabled,
    initialFocus: true,
  };

  return (
    <div className={className}>
      {label && (
        <label className="block text-secondary mb-1">{label}</label>
      )}
      <Popover>
        <PopoverTrigger asChild>
          <Button
            variant="outline"
            disabled={disabled}
            className={cn(
              "w-full justify-start text-left font-normal",
              !date && "text-muted-foreground"
            )}
          >
            <CalendarIcon className="mr-2 h-4 w-4" />
            {date ? format(date, "PPP") : <span>{placeholder}</span>}
          </Button>
        </PopoverTrigger>
        <PopoverContent className="w-auto p-0" align="start">
          <Calendar {...calendarProps} />
        </PopoverContent>
      </Popover>
    </div>
  );
} 