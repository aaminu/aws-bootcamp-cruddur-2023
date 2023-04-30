import './ProfileAvatar.css';

export default function ProfileAvatar(props) {
  if (!props.id) return;
  const backgroundImage = `url("https://assets.cruddur.aaminu.com/avatars/${props.id}.jpg")`;
  //console.log("asset url", backgroundImage);
  const styles = {
    backgroundImage: backgroundImage,
    backgroundSize: 'cover',
    backgroundPosition: 'center',
  };

  return (
    <div 
      className="profile-avatar"
      style={styles}
    ></div>
  );
} 