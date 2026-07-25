from supabase import Client, create_client

# -----------------------------------------------------------------------------
# 📌 SUPABASE CONFIGURATION (DIRECT HARDCODED)
# -----------------------------------------------------------------------------
SUPABASE_URL = "https://clriyqbkdxpjscpufqns.supabase.co"

SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImNscml5cWJrZHhwanNjcHVmcW5zIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODQ3NDEwMjcsImV4cCI6MjEwMDMxNzAyN30.sgslve6nIZ3h4gSHzHz8Ici9Zd-zbUkx5BPHEldaT2Q"

SUPABASE_SERVICE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImNscml5cWJrZHhwanNjcHVmcW5zIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc4NDc0MTAyNywiZXhwIjoyMTAwMzE3MDI3fQ.PpNmjWt6babeIB5b5ACghI7e633Cl0O1dtTsNWXPC_4"

# Standard Client for Auth (Login & Signup)
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Admin Client with elevated privileges (Profiles & RLS Bypass)
supabase_admin: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
