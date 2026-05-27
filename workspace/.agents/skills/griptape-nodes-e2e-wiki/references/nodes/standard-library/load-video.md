# LoadVideo

**Library:** Griptape Nodes Library **Class:** `LoadVideo` **Base class:** `DataNode` **Category:**
video **Display name:** Load Video

## Description

Loads video files into a workflow from a local file path or URL. The `video` and `path` parameters
are tethered — setting one updates the other. Accepts `.mp4`, `.avi`, `.mov`, `.mkv`, `.webm`,
`.flv`, `.wmv`, and `.m4v` files. Pure file loading with no external service dependencies.

## Parameters

| Name    | Type               | Modes                   | Default | Description                                   |
| ------- | ------------------ | ----------------------- | ------- | --------------------------------------------- |
| `video` | `VideoUrlArtifact` | INPUT, PROPERTY, OUTPUT | `None`  | The loaded video artifact.                    |
| `path`  | `str`              | PROPERTY, OUTPUT        | `""`    | Path to a local video file or URL to a video. |

## Use When

- You need a `VideoUrlArtifact` input for the node under test without external services.
- Set `path` to an absolute filesystem path or URL; the `video` output will carry the artifact.
- Wire `LoadVideo.video` → `NodeUnderTest.<video_input>`.

### Bundled test asset

A minimal color-bars video is bundled with this wiki for use in test workflows:

```
../../../assets/color_bars_video.mp4
```

This path is relative to this wiki page. Resolve it to an absolute path before passing it to
`SetParameterValueRequest` on the `path` parameter.

## Example Wiring

```
(set LoadVideo.path = "/absolute/path/to/color_bars_video.mp4" as PROPERTY)
LoadVideo.video  →  GetVideoMetadata.video
```
