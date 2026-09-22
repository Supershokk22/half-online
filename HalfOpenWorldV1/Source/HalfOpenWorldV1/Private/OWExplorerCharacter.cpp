#include "OWExplorerCharacter.h"

#include "Camera/CameraComponent.h"
#include "Components/CapsuleComponent.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "GameFramework/Controller.h"
#include "Components/InputComponent.h"

AOWExplorerCharacter::AOWExplorerCharacter()
{
    PrimaryActorTick.bCanEverTick = false;
    GetCapsuleComponent()->InitCapsuleSize(36.f, 88.f);
    GetCharacterMovement()->MaxWalkSpeed = 420.f;
    GetCharacterMovement()->JumpZVelocity = 440.f;
    GetCharacterMovement()->AirControl = 0.25f;
    bUseControllerRotationYaw = true;
    GetCharacterMovement()->bOrientRotationToMovement = false;
    EyeCamera = CreateDefaultSubobject<UCameraComponent>(TEXT("EyeCamera"));
    EyeCamera->SetupAttachment(GetCapsuleComponent());
    EyeCamera->SetRelativeLocation(FVector(0.f, 0.f, 64.f));
    EyeCamera->bUsePawnControlRotation = true;
}

void AOWExplorerCharacter::SetupPlayerInputComponent(UInputComponent* Input)
{
    Super::SetupPlayerInputComponent(Input);
    Input->BindAxis(TEXT("OW_MoveForward"), this, &AOWExplorerCharacter::MoveForward);
    Input->BindAxis(TEXT("OW_MoveRight"), this, &AOWExplorerCharacter::MoveRight);
    Input->BindAxis(TEXT("OW_Turn"), this, &AOWExplorerCharacter::LookYaw);
    Input->BindAxis(TEXT("OW_LookUp"), this, &AOWExplorerCharacter::LookPitch);
    Input->BindAction(TEXT("OW_Jump"), IE_Pressed, this, &AOWExplorerCharacter::StartJump);
    Input->BindAction(TEXT("OW_Jump"), IE_Released, this, &AOWExplorerCharacter::StopJump);
    Input->BindAction(TEXT("OW_Sprint"), IE_Pressed, this, &AOWExplorerCharacter::StartSprint);
    Input->BindAction(TEXT("OW_Sprint"), IE_Released, this, &AOWExplorerCharacter::StopSprint);
}

void AOWExplorerCharacter::MoveForward(float Value)
{
    if (Controller && !FMath::IsNearlyZero(Value))
        AddMovementInput(FRotationMatrix(FRotator(0.f, Controller->GetControlRotation().Yaw, 0.f)).GetUnitAxis(EAxis::X), Value);
}

void AOWExplorerCharacter::MoveRight(float Value)
{
    if (Controller && !FMath::IsNearlyZero(Value))
        AddMovementInput(FRotationMatrix(FRotator(0.f, Controller->GetControlRotation().Yaw, 0.f)).GetUnitAxis(EAxis::Y), Value);
}

void AOWExplorerCharacter::LookYaw(float Value) { AddControllerYawInput(Value); }
void AOWExplorerCharacter::LookPitch(float Value) { AddControllerPitchInput(Value); }
void AOWExplorerCharacter::StartJump() { Jump(); }
void AOWExplorerCharacter::StopJump() { StopJumping(); }
void AOWExplorerCharacter::StartSprint() { GetCharacterMovement()->MaxWalkSpeed = 690.f; }
void AOWExplorerCharacter::StopSprint() { GetCharacterMovement()->MaxWalkSpeed = 420.f; }
