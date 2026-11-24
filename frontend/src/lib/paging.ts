/** Rows per request for the paged logs (brews, tastings): a few rows of the card grid. */
export const PAGE_SIZE = 24

interface Paged<T> {
  items: T[]
  total: number
}

/** `getNextPageParam` for offset-paged endpoints: the next offset, or `undefined` when done. */
export function nextOffset<T>(last: Paged<T>, pages: Paged<T>[]): number | undefined {
  const loaded = pages.reduce((count, page) => count + page.items.length, 0)
  return loaded < last.total ? loaded : undefined
}

/** Every row loaded so far, across pages, in order. */
export function loadedItems<T>(data: { pages: Paged<T>[] } | undefined): T[] {
  return data?.pages.flatMap((page) => page.items) ?? []
}

/** Rows matching the filters on the server, whether loaded yet or not. */
export function totalOf(data: { pages: Paged<unknown>[] } | undefined): number {
  return data?.pages[0]?.total ?? 0
}
