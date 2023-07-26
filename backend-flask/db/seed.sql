-- this file was manually created
INSERT INTO public.users (display_name, email, handle, cognito_user_id)
VALUES
  (:'user1_name', :'user1_email', :'user1_username' ,'MOCK'),
  (:'user2_name', :'user2_email', :'user2_username' ,'MOCK'),
  ('Londo Mollari','lmollari@centari.com' ,'londo' ,'MOCK');

INSERT INTO public.activities (user_uuid, message, expires_at)
VALUES
  (
    (SELECT uuid from public.users WHERE users.handle = :'user1_username' LIMIT 1),
    'This was imported as seed data!',
    current_timestamp + interval '10 day'
  ),
    (
    (SELECT uuid from public.users WHERE users.handle = :'user2_username' LIMIT 1),
    'I am the other!',
    current_timestamp + interval '10 day'
  );