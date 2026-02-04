AFRAME.registerComponent('mouse-wheel-zoom', {
  schema: {
    minFov: {default: 20},
    maxFov: {default: 80},
    speed: {default: 1}
  },

  init: function () {
    this.camera = this.el.getObject3D('camera');
    this.onWheel = this.onWheel.bind(this);
    window.addEventListener('wheel', this.onWheel);
  },

  onWheel: function (e) {
    if (!this.camera) return;

    let fov = this.camera.fov;
    fov += e.deltaY * 0.05 * this.data.speed;
    fov = Math.max(this.data.minFov, Math.min(this.data.maxFov, fov));

    this.camera.fov = fov;
    this.camera.updateProjectionMatrix();
  },

  remove: function () {
    window.removeEventListener('wheel', this.onWheel);
  }
});