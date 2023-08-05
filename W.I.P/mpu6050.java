import processing.serial.*;

Serial myPort;
float pitch, roll;
PVector position;

PShape robotModel;
PImage texture;

void setup() {
  size(800, 600, P3D);
  robotModel = loadShape("robot_model.obj");     // Load the 3D model
  texture = loadImage("robot_texture.png");      // Load the texture image
  
  position = new PVector(0, 0, 0);

  String portName = Serial.list()[0]; // Adjust the index [0] to your connected Arduino port
  myPort = new Serial(this, portName, 9600);
}

void draw() {
  background(255);
  translate(width / 2, height / 2, 0);
  rotateX(PI / 3);  // Adjusting the horizontal rotation angle
  rotateY(PI / 4); // Adjusting the vertical rotation angle
  drawRobot();    // Draw the companion robot model

  if (myPort.available() > 0) {
    String data = myPort.readStringUntil('\n');
    if (data != null) {
      data = data.trim();
      if (data.length() > 2) {
        if (data.charAt(0) == 'P' && data.charAt(1) == ':') {
          pitch = float(data.substring(2));
        }
        if (data.charAt(0) == 'R' && data.charAt(1) == ':') {
          roll = float(data.substring(2));
        }
      }
    }
  }

  translate(width/2, height/2, 0);
  rotateX(radians(-pitch)); // Adjust the orientation based on pitch
  rotateY(radians(roll)); // Adjust the orientation based on roll

  // Draw your robot model here
  drawRobot();
}

void drawRobot() {
  // Modeli çiz
  shape(robotModel);
  beginShape();
  texture(texture);
  vertex(-50, -75, 0, 0, 0);
  vertex(50, -75, 0, 1, 0);
  vertex(50, 75, 0, 1, 1);
  vertex(-50, 75, 0, 0, 1);
  endShape(CLOSE);
}
