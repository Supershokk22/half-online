#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Character.h"
#include "OWExplorerCharacter.generated.h"

class UCameraComponent;

UCLASS()
class HALFOPENWORLDV1_API AOWExplorerCharacter : public ACharacter
{
    GENERATED_BODY()
public:
    AOWExplorerCharacter();
    virtual void SetupPlayerInputComponent(UInputComponent* PlayerInputComponent) override;

private:
    UPROPERTY(VisibleAnywhere)
    TObjectPtr<UCameraComponent> EyeCamera;

    void MoveForward(float Value);
    void MoveRight(float Value);
    void LookYaw(float Value);
    void LookPitch(float Value);
    void StartJump();
    void StopJump();
    void StartSprint();
    void StopSprint();
};
