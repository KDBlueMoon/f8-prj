export interface City {
  id: number
  name: string
  slug: string
  is_municipality: boolean
}

export interface Category {
  id: string
  name: string
  slug: string
}

export interface CategoryGroup {
  id: string
  group_name: string
  group_slug: string
  categories: Category[]
}
