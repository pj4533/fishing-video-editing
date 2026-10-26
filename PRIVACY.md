# Privacy

The Fishing Video Editing skill runs entirely on your own machine.

- **It collects no data.** The skill and its scripts don't collect, store, or transmit personal data, usage data, or
  your footage.
- **Your files stay local.** Video, audio, transcripts and every intermediate file are read and written only in the
  folders you point it at. Transcription runs locally through whisper.cpp; it calls no cloud speech API.
- **The only network use is optional model downloads**, which you run yourself during setup: the whisper.cpp models
  from Hugging Face, the RNNoise wind-filter model from GitHub, and, if you install the optional extras, the
  demucs/AudioSet and YOLO/VitTrack models from their public hosts. Those downloads send nothing about you or your
  footage.
- **There's no telemetry**: no analytics, tracking, or accounts.

Claude itself (the app or API you use the skill with) is covered by Anthropic's own privacy policy.

Questions: open an issue at https://github.com/pj4533/fishing-video-editing/issues.
