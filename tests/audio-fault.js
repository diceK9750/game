/* Test-only fault injection. Never referenced by production player.html. */
(function () {
  const Native = window.AudioContext || window.webkitAudioContext;
  const fault = new URLSearchParams(location.search).get('fault') || 'none';
  window.audioProbeCalls = [];
  if (!Native) return;
  class ProbeContext extends Native {
    // Force SDL's suspended-output branch as well as the Safari exception;
    // Chromium may otherwise start running immediately after the click.
    get state() { return fault === 'reject' ? 'suspended' : super.state; }
    constructor(...args) {
      super(...args);
      const create = this.createBuffer.bind(this);
      this.createBuffer = (channels, length, rate) => {
        const entry = {channels, length, rate, contextRate: this.sampleRate, state: this.state, fault};
        window.audioProbeCalls.push(entry);
        console.info('[audio probe]', entry);
        if (fault === 'reject') throw new DOMException('Sample rate is not in the supported range.', 'NotSupportedError');
        return create(channels, length, rate);
      };
    }
  }
  window.AudioContext = ProbeContext;
})();
