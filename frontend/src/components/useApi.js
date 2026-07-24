import { endpoints } from '../api/client'
import { useEffect, useState, useCallback } from 'react'

/**
 * useApi(fetcher, deps)
 *   fetcher: () => Promise<any>      -- typically () => endpoints.foo()
 *   deps:    any[]                    -- change-driven refetch
 *
 * Returns { data, loading, error, refetch }.
 */
export function useApi(fetcher, deps = []) {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  const refetch = useCallback(async () => {
    setLoading(true); setError(null)
    try {
      setData(await fetcher())
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps)

  useEffect(() => { refetch() }, [refetch])

  return { data, loading, error, refetch }
}

export { endpoints }
