SELECT 
    users.handle 
FROM public.users 
WHERE 
    users.cognito_user_id = %(cognito_id)s