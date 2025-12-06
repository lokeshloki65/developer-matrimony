let localStream;
let remoteStream;
let peerConnection;
const servers = {
    iceServers: [
        { urls: 'stun:stun.l.google.com:19302' },
        { urls: 'stun:stun1.l.google.com:19302' }
    ]
};

async function startVideoCall(participantId) {
    try {
        // Create room
        const token = localStorage.getItem('authToken');
        const response = await fetch(`${API_URL}/api/video-call/create-room`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ participantId })
        });
        
        const data = await response.json();
        
        if (!data.success) {
            throw new Error(data.error);
        }
        
        const roomId = data.roomId;
        
        // Get local media
        localStream = await navigator.mediaDevices.getUserMedia({
            video: true,
            audio: true
        });
        
        document.getElementById('local-video').srcObject = localStream;
        
        // Initialize peer connection
        await initializePeerConnection(roomId);
        
    } catch (error) {
        console.error('Error starting call:', error);
        alert('Failed to start call: ' + error.message);
    }
}

async function initializePeerConnection(roomId) {
    peerConnection = new RTCPeerConnection(servers);
    
    // Add local stream tracks
    localStream.getTracks().forEach(track => {
        peerConnection.addTrack(track, localStream);
    });
    
    // Handle remote stream
    peerConnection.ontrack = (event) => {
        if (!remoteStream) {
            remoteStream = new MediaStream();
            document.getElementById('remote-video').srcObject = remoteStream;
        }
        remoteStream.addTrack(event.track);
    };
    
    // Handle ICE candidates
    peerConnection.onicecandidate = (event) => {
        if (event.candidate) {
            sendIceCandidate(roomId, event.candidate);
        }
    };
    
    // Create and send offer
    const offer = await peerConnection.createOffer();
    await peerConnection.setLocalDescription(offer);
    
    // Save offer to Firestore
    await db.collection('video_rooms').doc(roomId).update({
        offer: {
            type: offer.type,
            sdp: offer.sdp
        }
    });
    
    // Listen for answer
    listenForAnswer(roomId);
}

function listenForAnswer(roomId) {
    db.collection('video_rooms').doc(roomId).onSnapshot(async (snapshot) => {
        const data = snapshot.data();
        
        if (data.answer && !peerConnection.currentRemoteDescription) {
            const answer = new RTCSessionDescription(data.answer);
            await peerConnection.setRemoteDescription(answer);
        }
    });
    
    // Listen for ICE candidates
    db.collection('video_rooms').doc(roomId)
        .collection('candidates').onSnapshot((snapshot) => {
            snapshot.docChanges().forEach(async (change) => {
                if (change.type === 'added') {
                    const candidate = new RTCIceCandidate(change.doc.data());
                    await peerConnection.addIceCandidate(candidate);
                }
            });
        });
}

async function answerCall(roomId) {
    try {
        // Get local media
        localStream = await navigator.mediaDevices.getUserMedia({
            video: true,
            audio: true
        });
        
        document.getElementById('local-video').srcObject = localStream;
        
        // Join room
        const token = localStorage.getItem('authToken');
        await fetch(`${API_URL}/api/video-call/join-room/${roomId}`, {
            method: 'POST',
            headers: { 'Authorization': `Bearer ${token}` }
        });
        
        // Initialize peer connection
        peerConnection = new RTCPeerConnection(servers);
        
        localStream.getTracks().forEach(track => {
            peerConnection.addTrack(track, localStream);
        });
        
        peerConnection.ontrack = (event) => {
            if (!remoteStream) {
                remoteStream = new MediaStream();
                document.getElementById('remote-video').srcObject = remoteStream;
            }
            remoteStream.addTrack(event.track);
        };
        
        peerConnection.onicecandidate = (event) => {
            if (event.candidate) {
                sendIceCandidate(roomId, event.candidate);
            }
        };
        
        // Get offer from Firestore
        const roomDoc = await db.collection('video_rooms').doc(roomId).get();
        const roomData = roomDoc.data();
        
        if (roomData.offer) {
            await peerConnection.setRemoteDescription(
                new RTCSessionDescription(roomData.offer)
            );
            
            // Create answer
            const answer = await peerConnection.createAnswer();
            await peerConnection.setLocalDescription(answer);
            
            // Save answer
            await db.collection('video_rooms').doc(roomId).update({
                answer: {
                    type: answer.type,
                    sdp: answer.sdp
                }
            });
        }
        
        // Listen for ICE candidates
        db.collection('video_rooms').doc(roomId)
            .collection('candidates').onSnapshot((snapshot) => {
                snapshot.docChanges().forEach(async (change) => {
                    if (change.type === 'added') {
                        const candidate = new RTCIceCandidate(change.doc.data());
                        await peerConnection.addIceCandidate(candidate);
                    }
                });
            });
        
    } catch (error) {
        console.error('Error answering call:', error);
    }
}

async function sendIceCandidate(roomId, candidate) {
    await db.collection('video_rooms').doc(roomId)
        .collection('candidates').add(candidate.toJSON());
}

async function endCall(roomId) {
    // Stop local stream
    if (localStream) {
        localStream.getTracks().forEach(track => track.stop());
    }
    
    // Close peer connection
    if (peerConnection) {
        peerConnection.close();
    }
    
    // Update room status
    const token = localStorage.getItem('authToken');
    await fetch(`${API_URL}/api/video-call/end-call/${roomId}`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` }
    });
    
    // Close video UI
    document.getElementById('video-call-modal').style.display = 'none';
}

// Toggle video/audio
function toggleVideo() {
    const videoTrack = localStream.getVideoTracks()[0];
    videoTrack.enabled = !videoTrack.enabled;
    document.getElementById('toggle-video-btn').textContent = 
        videoTrack.enabled ? '📹' : '📹❌';
}

function toggleAudio() {
    const audioTrack = localStream.getAudioTracks()[0];
    audioTrack.enabled = !audioTrack.enabled;
    document.getElementById('toggle-audio-btn').textContent = 
        audioTrack.enabled ? '🎤' : '🎤❌';
}