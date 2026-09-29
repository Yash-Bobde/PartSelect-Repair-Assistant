import { useEffect, useState } from 'react';
import { getInstallationGuide } from '../api/api';
import { youtubeId } from '../lib/parts';

// Installation guide for a part: { status: 'loading' | 'ready' | 'none', guide, videoId }.
export function useGuide(partNumber) {
  const [state, setState] = useState({ status: 'loading', guide: null, videoId: null });

  useEffect(() => {
    let alive = true;
    setState({ status: 'loading', guide: null, videoId: null });
    getInstallationGuide(partNumber).then((guide) => {
      if (!alive) return;
      setState(
        guide
          ? { status: 'ready', guide, videoId: youtubeId(guide.video_url) }
          : { status: 'none', guide: null, videoId: null }
      );
    });
    return () => {
      alive = false;
    };
  }, [partNumber]);

  return state;
}
