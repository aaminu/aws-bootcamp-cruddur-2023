import './HomeFeedPage.css';
import React from "react";


import DesktopNavigation from 'components/DesktopNavigation';
import DesktopSidebar from 'components/DesktopSidebar';
import ActivityFeed from 'components/ActivityFeed';
import ActivityForm from 'components/ActivityForm';
import ReplyForm from 'components/ReplyForm';
import { checkAuth, getAccessToken } from 'lib/CheckAuth';

//Honeycomb Tracing
// import { trace, context, } from '@opentelemetry/api';
// const tracer = trace.getTracer();

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
      //console.log(backend_url)
      //var startTime = performance.now()
      await getAccessToken();
      const access_token = localStorage.getItem("access_token");
      const res = await fetch(backend_url, {
        headers: {
          Authorization: `Bearer ${access_token}`
        },
        method: "GET"
      });
      // var endTime = performance.now()

      let resJson = await res.json();
      if (res.status === 200) {
        setActivities(resJson)
        // tracer.startActiveSpan('HomeFeedPageLoadData', hmfSpan => {
        //   // Add attributes to custom span
        //   hmfSpan.setAttribute('homeFeedPage.latency_MS', (endTime - startTime));
        //   hmfSpan.setAttribute('homeFeedPage.status', true);
        //   hmfSpan.end();
        // });
      } else {
        console.log(res)
        // tracer.startActiveSpan('HomeFeedPageLoadData', hmfSpan => {
        //   // Add attributes to custom span
        //   hmfSpan.setAttribute('homeFeedPage.latency_MS', (endTime - startTime));
        //   hmfSpan.setAttribute('homeFeedPage.status', false);
        //   hmfSpan.end();
        // });
      }
    } catch (err) {
      console.log(err);
    }
  };


  React.useEffect(() => {
    //prevents double call
    if (dataFetchedRef.current) return;
    dataFetchedRef.current = true;

    loadData();
    checkAuth(setUser);
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
        <div className='activity_feed'>
          <div className='activity_feed_heading'>
            <div className='title'>Home</div>
          </div>
          <ActivityFeed 
            setReplyActivity={setReplyActivity} 
            setPopped={setPoppedReply} 
            activities={activities} 
          />
        </div>
      </div>
      <DesktopSidebar user={user} />
    </article>
  );
}