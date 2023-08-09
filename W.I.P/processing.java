import processing.serial.*;

Serial arduino;

PShape botModel; // PShape to hold the loaded 3D model

void setup() {
    size(800, 600, P3D);
    arduino = new Serial(this, "COMx", 9600); // COMx yerine Arduino'nun bağlı olduğu portu yazın

    // Load the .obj model
    botModel = loadShape("bot.obj");
}

void draw() {
    background(255);
    translate(width / 2, height / 2); // Move the origin to the center

    // Update model's position based on data from Arduino
    if (arduino.available() > 0) {
        String data = arduino.readStringUntil('\n');
        if (data != null) {
            data = data.trim();
            if (data.startsWith("MODEL ")) {
                float pitch = float(data.substring(6)); // Extract pitch value
                // Update model's position
                botModel.translate(0, pitch * 5, 0); // Adjust the scale as needed
            }
        }
    }

    // Draw the 3D model
    shape(botModel);
}
