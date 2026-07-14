import { Button } from "@/components/ui/button"
import {
  Command,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
} from "@/components/ui/command"
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover"
import { cn } from "@/lib/utils"
import { Check, ChevronsUpDown, Plus } from "lucide-react"
import { useState } from "react"

interface CreatableComboboxProps {
  value: string
  onChange: (value: string) => void
  options: string[]
  placeholder?: string
}

/**
 * Free-text select. The beans API takes the roaster as a name and creates it if it is new
 * (case-insensitive), so the user must be able to type one that isn't in the list.
 */
export function CreatableCombobox({
  value,
  onChange,
  options,
  placeholder = "Select or type…",
}: CreatableComboboxProps) {
  const [open, setOpen] = useState(false)
  const [query, setQuery] = useState("")

  const isNew =
    query.trim().length > 0 &&
    !options.some((option) => option.toLowerCase() === query.trim().toLowerCase())

  function select(next: string) {
    onChange(next)
    setQuery("")
    setOpen(false)
  }

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        <Button
          type="button"
          variant="outline"
          role="combobox"
          aria-expanded={open}
          className={cn(
            "w-full justify-between font-normal",
            !value && "text-muted-foreground",
          )}
        >
          {value || placeholder}
          <ChevronsUpDown className="size-4 opacity-50" />
        </Button>
      </PopoverTrigger>

      <PopoverContent className="w-(--radix-popover-trigger-width) p-0" align="start">
        <Command>
          <CommandInput
            placeholder="Search or type a new one…"
            value={query}
            onValueChange={setQuery}
          />
          <CommandList>
            {!isNew ? <CommandEmpty>No match.</CommandEmpty> : null}
            {isNew ? (
              <CommandGroup>
                <CommandItem value={query} onSelect={() => select(query.trim())}>
                  <Plus className="size-4" />
                  Create “{query.trim()}”
                </CommandItem>
              </CommandGroup>
            ) : null}
            <CommandGroup>
              {options.map((option) => (
                <CommandItem key={option} value={option} onSelect={() => select(option)}>
                  <Check
                    className={cn("size-4", value === option ? "opacity-100" : "opacity-0")}
                  />
                  {option}
                </CommandItem>
              ))}
            </CommandGroup>
          </CommandList>
        </Command>
      </PopoverContent>
    </Popover>
  )
}
