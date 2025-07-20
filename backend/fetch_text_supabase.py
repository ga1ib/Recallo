def fetch_text_from_supabase(supabase, identifier_value, user_id, identifier_type="file_uuid"):
    """
    Fetch content from Supabase using either file_uuid or chunk_id.
    
    Args:
        supabase: Supabase client instance
        identifier_value: The UUID or chunk ID
        user_id: The user's ID
        identifier_type: "file_uuid" or "chunk_id" (default is "file_uuid")
    
    Returns:
        Content string if found, otherwise None
    """
    try:
        response = (
            supabase.table("documents")
            .select("content")
            .eq(identifier_type, identifier_value)
            .eq("user_id", user_id)
            .limit(1)
            .execute()
        )

        if response.data:
            print(response.data)
            return response.data[0]["content"]
        else:
            return None
    except Exception as e:
        print(f"Error fetching from Supabase: {e}")
        return None
