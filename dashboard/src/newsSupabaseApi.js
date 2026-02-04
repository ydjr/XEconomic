import { supabase } from "./supabaseClient"

export async function getAgencyVolumeLastNMonths(monthsBack = 12) {
  const { data, error } = await supabase.rpc("get_news_volume_by_agency_month", {
    months_back: monthsBack,
  })
  if (error) throw error
  return data || []
}
