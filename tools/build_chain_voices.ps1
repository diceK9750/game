# Generate original Japanese callouts as portable PCM assets (Windows System.Speech).
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Speech
$voiceDirectory = Join-Path $PSScriptRoot '../assets/voices/cute-v2'
New-Item -ItemType Directory -Force -Path $voiceDirectory | Out-Null
$lines = @{
  you = @(@('いく','よ！'), @('つながっ','た！'), @('いい','感じ！'), @('まだ','まだ！'), @('ぜっ','こうちょう！'), @('止まら','ない！'), @('フィー','バー！'))
  cpu = @(@('いく','わよ！'), @('見えた','わ！'), @('余裕','よ！'), @('負けない','わ！'), @('私の番','よ！'), @('止められ','ない！'), @('フィーバー','よ！'))
}
foreach ($owner in @('you', 'cpu')) {
  $speaker = New-Object System.Speech.Synthesis.SpeechSynthesizer
  try {
    $speaker.SelectVoice($(if ($owner -eq 'you') { 'Microsoft Sayaka' } else { 'Microsoft Ayumi' }))
    $speaker.Rate = 1
    $speaker.Volume = 85
    for ($level = 1; $level -le 7; $level++) {
      $speaker.SetOutputToWaveFile((Join-Path $voiceDirectory "$owner-$level.wav"))
      # Shape the attack and ending independently instead of speeding up a recording.
      $pitch = $(if ($owner -eq 'you') { 18 } else { 10 }) + [Math]::Min(4, $level - 1)
      $tailPitch = $(if ($owner -eq 'you') { 8 } else { 4 })
      $rate = $(if ($owner -eq 'you') { 112 } else { 106 })
      $head = [System.Security.SecurityElement]::Escape($lines[$owner][$level - 1][0])
      $tail = [System.Security.SecurityElement]::Escape($lines[$owner][$level - 1][1])
      $ssml = '<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="ja-JP"><prosody pitch="+' + $pitch + '%" rate="' + $rate + '%">' + $head + '<prosody pitch="+' + $tailPitch + '%" rate="96%">' + $tail + '</prosody></prosody></speak>'
      $speaker.SpeakSsml($ssml)
      $speaker.SetOutputToNull()
    }
  } finally { $speaker.Dispose() }
}
