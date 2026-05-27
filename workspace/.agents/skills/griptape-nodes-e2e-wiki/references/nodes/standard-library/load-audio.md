# LoadAudio

**Library:** Griptape Nodes Library **Class:** `LoadAudio` **Base class:** `DataNode` **Category:**
audio **Display name:** Load Audio

## Description

Loads audio files into a workflow from a local file path or URL. The `audio` and `path` parameters
are tethered — setting one updates the other. Accepts `.mp3`, `.wav`, `.ogg`, `.flac`, `.m4a`,
`.aac`, `.wma`, `.opus`, and `.webm` files. Pure file loading with no external service
dependencies.

## Parameters

| Name    | Type               | Modes                   | Default | Description                                    |
| ------- | ------------------ | ----------------------- | ------- | ---------------------------------------------- |
| `audio` | `AudioUrlArtifact` | INPUT, PROPERTY, OUTPUT | `None`  | The loaded audio artifact.                     |
| `path`  | `str`              | PROPERTY, OUTPUT        | `""`    | Path to a local audio file or URL to an audio. |

## Use When

- You need an `AudioUrlArtifact` input for the node under test without external services.
- Set `path` to an absolute filesystem path or URL; the `audio` output will carry the artifact.
- Wire `LoadAudio.audio` → `NodeUnderTest.<audio_input>`.

### Bundled test assets

Two audio files are bundled with this wiki for use in test workflows:

| File                      | Format | Relative path from this page              |
| ------------------------- | ------ | ----------------------------------------- |
| `welcome_to_griptape.mp3` | MP3    | `../../../assets/welcome_to_griptape.mp3` |
| `welcome_to_griptape.wav` | WAV    | `../../../assets/welcome_to_griptape.wav` |

These paths are relative to this wiki page. Resolve to an absolute path before passing to
`SetParameterValueRequest` on the `path` parameter. Prefer the `.mp3` file for general testing
(smaller); use `.wav` when testing WAV-specific behaviour.

## Example Wiring

```
(set LoadAudio.path = "/absolute/path/to/welcome_to_griptape.mp3" as PROPERTY)
LoadAudio.audio  →  AudioDetails.audio
```
