var slider_img = document.querySelector('.slider-img');
var images = ['1.png', '2.png', '3.png', '4.png', '5.png'];
var i = 0; // Current Image Index

function prev() {
  if (i <= 0) i = images.length;
  i--;
  return setImg();
}

function next() {}

function goTo(imageNo) {}

function setImg() {
  return slider_img.setAttribute(
    'src',
    'static/assets/home_slider/' + images[i]
  );
}
