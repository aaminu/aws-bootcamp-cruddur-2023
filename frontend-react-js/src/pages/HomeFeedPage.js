import './HomeFeedPage.css';
import React from "react";

import DesktopNavigation  from '../components/DesktopNavigation';
import DesktopSidebar     from '../components/DesktopSidebar';
import ActivityFeed from '../components/ActivityFeed';
import ActivityForm from '../components/ActivityForm';
import ReplyForm from '../components/ReplyForm';

// [TODO] Authenication
import Cookies from 'js-cookie'

//Honeycomb Tracing
import { trace, context, } from '@opentelemetry/api';
const tracer = trace.getTracer();

export default function HomeFeedPage() {
  const [activities, setActivities] = React.useState([]);
  const [popped, setPopped] = React.useState(false);
  const [poppedReply, setPoppedReply] = React.useState(false);
  const [replyActivity, setReplyActivity] = React.useState({});
  const [user, setUser] = React.useState(null);
  const dataFetchedRef = React.useRef(false);

  const loadData = async () => {
    try {
      const backend_url = `${process.env.REACT_APP_BACKEND_URL}/api/activities/home`
      var startTime = performance.now()
      const res = await fetch(backend_url, {
        method: "GET"
      });
      var endTime = performance.now()

      let resJson = await res.json();
      if (res.status === 200) {
        setActivities(resJson)
        tracer.startActiveSpan('HomeFeedPageLoadSpan', hmfSpan => {
          // Add your attributes to describe the button clicked here
          hmfSpan.setAttribute('homeeFeedPage.latency_MS', (endTime - startTime));
          hmfSpan.setAttribute('homeeFeedPage.status', true);
          hmfSpan.end();
        });
      } else {
        console.log(res)
        tracer.startActiveSpan('HomeFeedPageLoadSpan', hmfSpan => {
          // Add your attributes to describe the button clicked here
          hmfSpan.setAttribute('homeeFeedPage.latency_MS', (endTime - startTime));
          hmfSpan.setAttribute('homeeFeedPage.status', false);
          hmfSpan.end();
        });
      }
    } catch (err) {
      console.log(err);
    }
  };

  const checkAuth = async () => {
    console.log('checkAuth')
    // [TODO] Authenication
    if (Cookies.get('user.logged_in')) {
      setUser({
        display_name: Cookies.get('user.name'),
        handle: Cookies.get('user.username')
      })
    }
  };

  React.useEffect(()=>{
    //prevents double call
    if (dataFetchedRef.current) return;
    dataFetchedRef.current = true;

    loadData();
    checkAuth();
  }, [])

  return (
    <article>
      <DesktopNavigation user={user} active={'home'} setPopped={setPopped} />
      <div className='content'>
        <ActivityForm  
          popped={popped}
          setPopped={setPopped} 
          setActivities={setActivities} 
        />
        <ReplyForm 
          activity={replyActivity} 
          popped={poppedReply} 
          setPopped={setPoppedReply} 
          setActivities={setActivities} 
          activities={activities} 
        />
        <ActivityFeed 
          title="Home" 
          setReplyActivity={setReplyActivity} 
          setPopped={setPoppedReply} 
          activities={activities} 
        />
      </div>
      <DesktopSidebar user={user} />
    </article>
  );
}